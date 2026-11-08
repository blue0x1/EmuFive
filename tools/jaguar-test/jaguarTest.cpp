// Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
// Checks KytyPS5's Jaguar replacements (src/loader/jaguarCompat.cpp) on a CPU that has AVX2,
// FMA and BMI2: every AVX2/FMA/BMI2 instruction form found in the given code files runs
// natively and as its replacement from the same random state, and all registers, flags and
// memory must match. It also checks that no replacement uses AVX2, FMA or BMI2 itself.
//   jaguarTest [-n instances-per-form] [-r runs] code.bin...

#include "loader/jaguarCompat.h"

#include <Zydis/Zydis.h>
#include <algorithm>
#include <cmath>
#include <csetjmp>
#include <csignal>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <random>
#include <string>
#include <sys/mman.h>
#include <vector>
#include <xbyak/xbyak.h>

using namespace Xbyak::util;

struct State {
	uint64_t gpr[16];
	uint64_t flags;
	uint64_t host_rsp;
	uint64_t pad[6];
	uint8_t  ymm[16][32];
};

constexpr size_t AreaSize  = 64 * 1024;
constexpr size_t CodeSize  = 1024 * 1024;
constexpr uint64_t Status  = 0x8d5; // CF PF AF ZF SF OF

static uint8_t* Map(size_t size) {
	void* p = mmap(nullptr, size, PROT_READ | PROT_WRITE | PROT_EXEC,
	               MAP_PRIVATE | MAP_ANONYMOUS | MAP_32BIT, -1, 0);
	if (p == MAP_FAILED) {
		perror("mmap");
		exit(1);
	}
	return static_cast<uint8_t*>(p);
}

static State*   g_state;
static uint8_t* g_data;
static uint8_t* g_stack;
static uint8_t* g_native_code;
static uint8_t* g_repl_code;

static sigjmp_buf g_jump;
static volatile int g_signal;
static void OnSignal(int sig, siginfo_t*, void*) {
	g_signal = sig;
	siglongjmp(g_jump, 1);
}

static Xbyak::Address At(const void* p) {
	return Xbyak::util::ptr[Xbyak::RegExp(reinterpret_cast<size_t>(p))];
}

// Loads the state, runs `body`, saves the state.
template <typename Body>
static void BuildRunner(Xbyak::CodeGenerator& g, Body body) {
	const Xbyak::Reg64 regs[16] = {rax, rcx, rdx, rbx, rsp, rbp, rsi, rdi,
	                               r8,  r9,  r10, r11, r12, r13, r14, r15};
	g.reset();
	for (auto r: {rbx, rbp, r12, r13, r14, r15}) {
		g.push(r);
	}
	g.mov(At(&g_state->host_rsp), rsp);
	for (int i = 0; i < 16; ++i) {
		g.vmovdqu(Xbyak::Ymm(i), At(g_state->ymm[i]));
	}
	g.push(Xbyak::util::qword[Xbyak::RegExp(reinterpret_cast<size_t>(&g_state->flags))]);
	g.popfq();
	g.mov(rsp, At(&g_state->gpr[4]));
	for (int i = 0; i < 16; ++i) {
		if (i != 4) {
			g.mov(regs[i], At(&g_state->gpr[i]));
		}
	}
	body();
	for (int i = 0; i < 16; ++i) {
		g.mov(At(&g_state->gpr[i]), regs[i]);
	}
	g.mov(rsp, At(&g_state->host_rsp));
	g.pushfq();
	g.pop(rax);
	g.mov(At(&g_state->flags), rax);
	for (int i = 0; i < 16; ++i) {
		g.vmovdqu(At(g_state->ymm[i]), Xbyak::Ymm(i));
	}
	for (auto r: {r15, r14, r13, r12, rbp, rbx}) {
		g.pop(r);
	}
	g.vzeroupper();
	g.ret();
}

struct Instance {
	std::vector<uint8_t> bytes;
	std::string          form;
};

static std::string FormOf(const ZydisDecodedInstruction& in, const ZydisDecodedOperand* ops) {
	std::string s = ZydisMnemonicGetString(in.mnemonic);
	for (int i = 0; i < in.operand_count_visible; ++i) {
		s += i ? "," : " ";
		const auto& o = ops[i];
		if (o.type == ZYDIS_OPERAND_TYPE_REGISTER) {
			const auto c = ZydisRegisterGetClass(o.reg.value);
			s += c == ZYDIS_REGCLASS_YMM ? "y" : c == ZYDIS_REGCLASS_XMM ? "x" : "r" + std::to_string(o.size);
		} else if (o.type == ZYDIS_OPERAND_TYPE_MEMORY) {
			s += "m" + std::to_string(o.size);
		} else {
			s += "i";
		}
	}
	return s;
}

struct Result {
	long runs = 0, failures = 0, inexact = 0, faults = 0, unsupported = 0, bad_isa = 0;
	std::string first_failure;
};

int main(int argc, char** argv) {
	int per_form = 20;
	const char* only = std::getenv("ONLY"); // Test only forms containing this text, verbosely.
	int runs     = 40;
	std::vector<std::string> files;
	for (int i = 1; i < argc; ++i) {
		if (!strcmp(argv[i], "-n") && i + 1 < argc) {
			per_form = atoi(argv[++i]);
		} else if (!strcmp(argv[i], "-r") && i + 1 < argc) {
			runs = atoi(argv[++i]);
		} else {
			files.push_back(argv[i]);
		}
	}

	ZydisDecoder decoder;
	ZydisDecoderInit(&decoder, ZYDIS_MACHINE_MODE_LONG_64, ZYDIS_STACK_WIDTH_64);

	// Collect instances of each form (reservoir sampling for variety).
	std::mt19937_64                               rng(12345);
	std::map<std::string, std::vector<Instance>>  forms;
	std::map<std::string, long>                   seen;
	for (const auto& file: files) {
		FILE* f = fopen(file.c_str(), "rb");
		if (!f) {
			perror(file.c_str());
			return 1;
		}
		std::vector<uint8_t> code;
		for (int c; (c = fgetc(f)) != EOF;) {
			code.push_back(static_cast<uint8_t>(c));
		}
		fclose(f);
		ZydisDecodedInstruction in;
		ZydisDecodedOperand     ops[ZYDIS_MAX_OPERAND_COUNT];
		for (size_t off = 0; off < code.size();) {
			if (!ZYAN_SUCCESS(ZydisDecoderDecodeFull(&decoder, code.data() + off, code.size() - off,
			                                         &in, ops))) {
				++off;
				continue;
			}
			if (Loader::JaguarCompat::IsMissing(in)) {
				Instance instance {{code.begin() + off, code.begin() + off + in.length},
				                   FormOf(in, ops)};
				auto& list = forms[instance.form];
				long  n    = ++seen[instance.form];
				if (static_cast<int>(list.size()) < per_form) {
					list.push_back(instance);
				} else if (long slot = static_cast<long>(rng() % n); slot < per_form) {
					list[slot] = instance;
				}
			}
			off += in.length;
		}
	}

	g_state       = reinterpret_cast<State*>(Map(4096));
	g_data        = Map(AreaSize);
	g_stack       = Map(AreaSize);
	g_native_code = Map(CodeSize);
	g_repl_code   = Map(CodeSize);
	Xbyak::CodeGenerator native(CodeSize, g_native_code);
	Xbyak::CodeGenerator repl(CodeSize, g_repl_code);

	struct sigaction sa {};
	sa.sa_sigaction = OnSignal;
	sa.sa_flags     = SA_SIGINFO | SA_NODEFER;
	sigaction(SIGSEGV, &sa, nullptr);
	sigaction(SIGILL, &sa, nullptr);
	sigaction(SIGBUS, &sa, nullptr);
	sigaction(SIGFPE, &sa, nullptr);

	std::vector<uint8_t> data0(AreaSize), stack0(AreaSize), data1(AreaSize), stack1(AreaSize);
	State                state0 {}, state1 {};
	std::map<std::string, Result> results;
	long total_instances = 0;

	for (auto& [form, instances]: forms) {
		if (only != nullptr && form.find(only) == std::string::npos) {
			continue;
		}
		auto& result = results[form];
		for (const auto& instance: instances) {
			ZydisDecodedInstruction in;
			ZydisDecodedOperand     ops[ZYDIS_MAX_OPERAND_COUNT];
			ZydisDecoderDecodeFull(&decoder, instance.bytes.data(), instance.bytes.size(), &in, ops);
			const bool bzhi = in.mnemonic == ZYDIS_MNEMONIC_BZHI;
			const bool fma  = in.meta.isa_ext == ZYDIS_ISA_EXT_FMA;

			// Memory operand: where it should point.
			int mem = -1;
			for (int i = 0; i < in.operand_count_visible; ++i) {
				if (ops[i].type == ZYDIS_OPERAND_TYPE_MEMORY) {
					mem = i;
				}
			}
			if (mem >= 0 && ops[mem].mem.base == ZYDIS_REGISTER_NONE) {
				continue; // Absolute address.
			}
			++total_instances;
			const uint64_t data_target  = reinterpret_cast<uint64_t>(g_data) + AreaSize / 2;
			const uint64_t stack_middle = reinterpret_cast<uint64_t>(g_stack) + AreaSize / 2;

			// Native: the instruction re-encoded in place (RIP-relative operands aimed at data).
			uint64_t native_address = 0;
			bool     encode_ok      = true;
			BuildRunner(native, [&] {
				native_address = reinterpret_cast<uint64_t>(native.getCurr());
				ZydisEncoderRequest request;
				ZydisEncoderDecodedInstructionToEncoderRequest(&in, ops, in.operand_count_visible,
				                                               &request);
				if (mem >= 0 && ops[mem].mem.base == ZYDIS_REGISTER_RIP) {
					request.operands[mem].mem.displacement = static_cast<ZyanI64>(data_target);
				}
				uint8_t   code[16];
				ZyanUSize size = sizeof(code);
				if (!ZYAN_SUCCESS(ZydisEncoderEncodeInstructionAbsolute(&request, code, &size,
				                                                         native_address))) {
					encode_ok = false;
					return;
				}
				native.db(code, size);
			});
			if (!encode_ok) {
				result.unsupported++;
				continue;
			}
			ZydisDecodedInstruction placed;
			ZydisDecodedOperand     placed_ops[ZYDIS_MAX_OPERAND_COUNT];
			ZydisDecoderDecodeFull(&decoder, reinterpret_cast<void*>(native_address), 16, &placed,
			                       placed_ops);

			for (bool flags_live: {true, false}) {
				bool     generated = true;
				uint64_t repl_begin = 0, repl_end = 0;
				Xbyak::ClearError();
				BuildRunner(repl, [&] {
					repl_begin = reinterpret_cast<uint64_t>(repl.getCurr());
					generated  = Loader::JaguarCompat::Generate(placed, placed_ops, native_address,
					                                            repl, flags_live);
					repl_end   = reinterpret_cast<uint64_t>(repl.getCurr());
				});
				if (!generated || Xbyak::GetError() != 0) {
					result.unsupported++;
					if (result.first_failure.empty()) {
						result.first_failure = "not supported";
					}
					break;
				}
				// The replacement must only use what the Jaguar has.
				for (uint64_t p = repl_begin; p < repl_end;) {
					ZydisDecodedInstruction r;
					if (!ZYAN_SUCCESS(ZydisDecoderDecodeInstruction(&decoder, nullptr,
					                                                reinterpret_cast<void*>(p),
					                                                repl_end - p, &r))) {
						++p;
						continue;
					}
					if (Loader::JaguarCompat::IsMissing(r) ||
					    r.meta.isa_ext == ZYDIS_ISA_EXT_AVX512EVEX ||
					    r.encoding == ZYDIS_INSTRUCTION_ENCODING_EVEX) {
						result.bad_isa++;
						if (result.first_failure.empty()) {
							result.first_failure = std::string("replacement uses ") +
							                       ZydisMnemonicGetString(r.mnemonic);
						}
					}
					// Skip data that the replacement jumps over.
					if (r.mnemonic == ZYDIS_MNEMONIC_JMP && r.raw.imm[0].is_relative) {
						const uint64_t target = p + r.length + r.raw.imm[0].value.s;
						if (target > p && target <= repl_end) {
							p = target;
							continue;
						}
					}
					p += r.length;
				}

				for (int run = 0; run < runs; ++run) {
					// Random state.
					State s {};
					for (auto& v: s.gpr) {
						switch (rng() % 3) {
							case 0: v = rng() % 80; break;
							case 1: v = rng() % 0x100000000ULL; break;
							default: v = rng(); break;
						}
					}
					s.flags = 0x202 | (rng() & Status);
					for (auto& reg: s.ymm) {
						for (int lane = 0; lane < 8; ++lane) {
							uint32_t v = 0;
							float    fv;
							switch (rng() % 6) {
								case 0: v = rng() % 70; break;
								case 1: v = static_cast<uint32_t>(rng()); break;
								case 2:
									fv = std::uniform_real_distribution<float>(-100, 100)(rng);
									memcpy(&v, &fv, 4);
									break;
								case 3: {
									static const uint32_t special[] = {
									    0, 0x80000000, 0x3f800000, 0xbf800000, 0x7f800000,
									    0xff800000, 0x7fc00000, 0x00000001, 0x007fffff, 0x7f7fffff};
									v = special[rng() % 10];
									break;
								}
								case 4: {
									double d = std::uniform_real_distribution<double>(-100, 100)(rng);
									memcpy(reg + lane * 4, &d, 8);
									lane++;
									continue;
								}
								default: v = static_cast<uint32_t>(rng() % 0x100); break;
							}
							memcpy(reg + lane * 4, &v, 4);
						}
					}
					s.gpr[4] = stack_middle;
					if (mem >= 0 && placed_ops[mem].mem.base != ZYDIS_REGISTER_RIP) {
						const auto& m     = placed_ops[mem].mem;
						const int   base  = ZydisRegisterGetId(
                            ZydisRegisterGetLargestEnclosing(ZYDIS_MACHINE_MODE_LONG_64, m.base));
						const auto  index_class = ZydisRegisterGetClass(m.index);
						const bool  vsib = index_class == ZYDIS_REGCLASS_XMM || index_class == ZYDIS_REGCLASS_YMM;
						if (vsib) {
							// Gathers: small signed indices, so every element is near data_target.
							const bool qwords = in.mnemonic == ZYDIS_MNEMONIC_VGATHERQPS ||
							                    in.mnemonic == ZYDIS_MNEMONIC_VGATHERQPD ||
							                    in.mnemonic == ZYDIS_MNEMONIC_VPGATHERQD ||
							                    in.mnemonic == ZYDIS_MNEMONIC_VPGATHERQQ;
							uint8_t* lanes = s.ymm[ZydisRegisterGetId(m.index)];
							for (int lane = 0; lane < (qwords ? 4 : 8); ++lane) {
								const int64_t v = static_cast<int64_t>(rng() % 64) - 32;
								if (qwords) {
									memcpy(lanes + lane * 8, &v, 8);
								} else {
									const int32_t v32 = static_cast<int32_t>(v);
									memcpy(lanes + lane * 4, &v32, 4);
								}
							}
						}
						const int   index = m.index == ZYDIS_REGISTER_NONE || vsib
						                        ? -1
						                        : ZydisRegisterGetId(ZydisRegisterGetLargestEnclosing(
						                              ZYDIS_MACHINE_MODE_LONG_64, m.index));
						const int64_t scale = index < 0 ? 0 : m.scale;
						const int64_t disp  = m.disp.value;
						if (base == 4) {
							if (index >= 0) {
								s.gpr[index] = (64 / scale) * (rng() % 4);
							}
						} else if (index == base) {
							s.gpr[base] = (data_target - disp) / (1 + scale);
						} else {
							if (index >= 0) {
								s.gpr[index] = (64 / scale) * (rng() % 4);
							}
							s.gpr[base] = data_target - disp - (index >= 0 ? s.gpr[index] * scale : 0);
						}
					}
					for (auto& b: data0) {
						b = static_cast<uint8_t>(rng());
					}
					for (auto& b: stack0) {
						b = static_cast<uint8_t>(rng());
					}

					auto run_one = [&](uint8_t* code, State* out, std::vector<uint8_t>& data_out,
					                   std::vector<uint8_t>& stack_out) -> bool {
						*g_state = s;
						memcpy(g_data, data0.data(), AreaSize);
						memcpy(g_stack, stack0.data(), AreaSize);
						g_signal = 0;
						if (sigsetjmp(g_jump, 1) != 0) {
							return false;
						}
						reinterpret_cast<void (*)()>(code)();
						*out = *g_state;
						memcpy(data_out.data(), g_data, AreaSize);
						memcpy(stack_out.data(), g_stack, AreaSize);
						return true;
					};
					std::vector<uint8_t> data_n(AreaSize), stack_n(AreaSize);
					const bool native_ok = run_one(g_native_code, &state0, data_n, stack_n);
					const bool repl_ok   = run_one(g_repl_code, &state1, data1, stack1);
					if (!native_ok) {
						result.faults++;
						break;
					}
					result.runs++;
					std::string why;
					if (!repl_ok) {
						why = "replacement faulted (signal " + std::to_string(g_signal) + ")";
					} else {
						for (int i = 0; i < 16 && why.empty(); ++i) {
							if (state0.gpr[i] != state1.gpr[i]) {
								char buf[128];
								snprintf(buf, sizeof buf, "gpr%d %016llx vs %016llx", i,
								         (unsigned long long)state0.gpr[i],
								         (unsigned long long)state1.gpr[i]);
								why = buf;
							}
						}
						const uint64_t mask = bzhi ? 0x8c1 : (Status | 0x400);
						if (why.empty() && flags_live && ((state0.flags ^ state1.flags) & mask)) {
							char buf[96];
							snprintf(buf, sizeof buf, "flags %llx vs %llx",
							         (unsigned long long)state0.flags, (unsigned long long)state1.flags);
							why = buf;
						}
						if (why.empty() && data_n != data1) {
							why = "data memory differs";
						}
						// Below the 128-byte red zone is free for anyone to use (signal handlers,
						// the replacements' own saves): compare from rsp-128 up.
						constexpr size_t Owned = AreaSize / 2 - 128;
						if (why.empty() && memcmp(stack_n.data() + Owned, stack1.data() + Owned,
						                          AreaSize - Owned) != 0) {
							size_t i = Owned;
							while (stack_n[i] == stack1[i]) {
								++i;
							}
							why = "stack memory differs at rsp" +
							      std::to_string(static_cast<long>(i) - static_cast<long>(AreaSize / 2));
						}
						for (int r = 0; r < 16 && why.empty(); ++r) {
							if (memcmp(state0.ymm[r], state1.ymm[r], 32) != 0) {
								// FMA in single precision may differ in the last bit in rare cases.
								bool close = fma;
								for (int lane = 0; close && lane < 8; ++lane) {
									int32_t a, b;
									memcpy(&a, state0.ymm[r] + lane * 4, 4);
									memcpy(&b, state1.ymm[r] + lane * 4, 4);
									if (std::abs(static_cast<long>(a) - static_cast<long>(b)) > 1) {
										close = false;
									}
								}
								if (close) {
									result.inexact++;
								} else {
									why = "ymm" + std::to_string(r) + " differs";
									if (only != nullptr) {
										printf("%s: ymm%d\n", form.c_str(), r);
										for (int q = 0; q < 16; ++q) {
											printf(" in ymm%-2d", q);
											for (int lane = 0; lane < 4; ++lane) {
												uint32_t v;
												memcpy(&v, s.ymm[q] + lane * 4, 4);
												printf(" %08x", v);
											}
											printf("\n");
										}
										for (const auto* st: {&state0, &state1}) {
											printf(" out     ");
											for (int lane = 0; lane < 4; ++lane) {
												uint32_t v;
												memcpy(&v, st->ymm[r] + lane * 4, 4);
												printf(" %08x", v);
											}
											printf("\n");
										}
									}
								}
							}
						}
					}
					if (!why.empty()) {
						result.failures++;
						if (result.first_failure.empty()) {
							char hex[64] = {};
							for (size_t i = 0; i < instance.bytes.size(); ++i) {
								snprintf(hex + i * 3, 4, "%02x ", instance.bytes[i]);
							}
							result.first_failure = why + (flags_live ? " [flags live] " : " ") + hex;
						}
					}
				}
			}
		}
	}

	long forms_ok = 0, forms_bad = 0, runs_total = 0, inexact_total = 0;
	for (const auto& [form, r]: results) {
		runs_total += r.runs;
		inexact_total += r.inexact;
		const bool bad = r.failures || r.unsupported || r.bad_isa;
		bad ? ++forms_bad : ++forms_ok;
		if (bad || r.faults || r.inexact) {
			printf("%-40s runs=%-6ld fail=%-4ld unsupported=%-3ld bad_isa=%-3ld inexact=%-4ld "
			       "native_faults=%-3ld %s\n",
			       form.c_str(), r.runs, r.failures, r.unsupported, r.bad_isa, r.inexact, r.faults,
			       r.first_failure.c_str());
		}
	}
	printf("\nforms: %zu (%ld pass, %ld fail), instances: %ld, runs: %ld, inexact FMA lanes: %ld\n",
	       results.size(), forms_ok, forms_bad, total_instances, runs_total, inexact_total);
	return forms_bad == 0 ? 0 : 1;
}
