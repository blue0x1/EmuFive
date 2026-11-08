# Copyright (C) 2026 Chokri Hammedi (blue0x1) <https://github.com/blue0x1>
"""Screenshots of the X screen (:0) through libX11 (ctypes) and pygame, with no other tools.

A fullscreen game hands its frames straight to the display, so the screen copy that XGetImage
reads stops changing. A 1x1 window over the top-left corner for half a second makes the game
draw through the normal path again, so the picture is the current one."""

import ctypes
import os
import time

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame  # noqa: E402


class _XWindowAttributes(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int), ("y", ctypes.c_int), ("width", ctypes.c_int), ("height", ctypes.c_int),
                ("border_width", ctypes.c_int), ("depth", ctypes.c_int), ("visual", ctypes.c_void_p),
                ("root", ctypes.c_ulong), ("pad", ctypes.c_byte * 200)]


class _XImage(ctypes.Structure):
    _fields_ = [("width", ctypes.c_int), ("height", ctypes.c_int), ("xoffset", ctypes.c_int),
                ("format", ctypes.c_int), ("data", ctypes.POINTER(ctypes.c_ubyte)), ("byte_order", ctypes.c_int),
                ("bitmap_unit", ctypes.c_int), ("bitmap_bit_order", ctypes.c_int), ("bitmap_pad", ctypes.c_int),
                ("depth", ctypes.c_int), ("bytes_per_line", ctypes.c_int), ("bits_per_pixel", ctypes.c_int)]


class _XSetWindowAttributes(ctypes.Structure):
    _fields_ = [("background_pixmap", ctypes.c_ulong), ("background_pixel", ctypes.c_ulong),
                ("border_pixmap", ctypes.c_ulong), ("border_pixel", ctypes.c_ulong),
                ("bit_gravity", ctypes.c_int), ("win_gravity", ctypes.c_int), ("backing_store", ctypes.c_int),
                ("backing_planes", ctypes.c_ulong), ("backing_pixel", ctypes.c_ulong),
                ("save_under", ctypes.c_int), ("event_mask", ctypes.c_long),
                ("do_not_propagate_mask", ctypes.c_long), ("override_redirect", ctypes.c_int),
                ("colormap", ctypes.c_ulong), ("cursor", ctypes.c_ulong)]


def _x11():
    x11 = ctypes.cdll.LoadLibrary("libX11.so.6")
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    x11.XDefaultRootWindow.restype = ctypes.c_ulong
    x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
    x11.XGetWindowAttributes.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(_XWindowAttributes)]
    x11.XGetImage.restype = ctypes.POINTER(_XImage)
    x11.XGetImage.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_int, ctypes.c_uint,
                              ctypes.c_uint, ctypes.c_ulong, ctypes.c_int]
    x11.XDestroyImage = None
    x11.XCreateWindow.restype = ctypes.c_ulong
    x11.XCreateWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_int, ctypes.c_int, ctypes.c_uint,
                                  ctypes.c_uint, ctypes.c_uint, ctypes.c_int, ctypes.c_uint, ctypes.c_void_p,
                                  ctypes.c_ulong, ctypes.POINTER(_XSetWindowAttributes)]
    x11.XMapRaised.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    x11.XDestroyWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    x11.XFree.argtypes = [ctypes.c_void_p]
    return x11


def capture(path, display=b":0"):
    """Saves the screen as a PNG at `path`. Returns True on success."""
    x11 = _x11()
    d = x11.XOpenDisplay(display)
    if not d:
        return False
    try:
        root = x11.XDefaultRootWindow(d)
        swa = _XSetWindowAttributes()
        swa.override_redirect = 1
        dot = x11.XCreateWindow(d, root, 0, 0, 1, 1, 0, 0, 1, None, (1 << 9) | (1 << 1), ctypes.byref(swa))
        x11.XMapRaised(d, dot)
        x11.XSync(d, 0)
        time.sleep(0.5)
        attrs = _XWindowAttributes()
        x11.XGetWindowAttributes(d, root, ctypes.byref(attrs))
        image_ptr = x11.XGetImage(d, root, 0, 0, attrs.width, attrs.height, 0xFFFFFFFF, 2)
        x11.XDestroyWindow(d, dot)
        x11.XSync(d, 0)
        if not image_ptr:
            return False
        image = image_ptr.contents
        raw = ctypes.string_at(image.data, image.bytes_per_line * image.height)
        surface = pygame.image.frombuffer(raw, (image.width, image.height), "BGRA")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        pygame.image.save(surface, path)
        return True
    finally:
        x11.XCloseDisplay(d)
