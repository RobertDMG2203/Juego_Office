"""Bloqueo de atajos del sistema para Windows.

Es una defensa de conveniencia dentro de una sesión educativa, no un límite de
seguridad del sistema operativo. Ctrl+Alt+Supr pertenece al escritorio seguro
de Windows y no puede bloquearse desde una aplicación normal.
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes


class WindowsShortcutBlocker:
    def __init__(self):
        self.hook = None
        self.callback = None

    def install(self) -> bool:
        if sys.platform != "win32":
            return False

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        WH_KEYBOARD_LL, HC_ACTION = 13, 0
        WM_KEYDOWN, WM_SYSKEYDOWN = 0x0100, 0x0104
        VK_TAB, VK_ESCAPE = 0x09, 0x1B
        VK_LWIN, VK_RWIN = 0x5B, 0x5C
        VK_CONTROL, VK_MENU = 0x11, 0x12
        VK_LEFT, VK_RIGHT, VK_D = 0x25, 0x27, 0x44

        class KBDLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [
                ("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_void_p),
            ]

        LowLevelProc = ctypes.WINFUNCTYPE(
            ctypes.c_ssize_t, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
        )
        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE
        user32.SetWindowsHookExW.argtypes = [ctypes.c_int, LowLevelProc, wintypes.HINSTANCE, wintypes.DWORD]
        user32.SetWindowsHookExW.restype = wintypes.HANDLE
        user32.CallNextHookEx.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
        user32.CallNextHookEx.restype = ctypes.c_ssize_t
        user32.UnhookWindowsHookEx.argtypes = [wintypes.HANDLE]
        user32.UnhookWindowsHookEx.restype = wintypes.BOOL

        def keyboard_proc(code, wparam, lparam):
            if code == HC_ACTION and wparam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                info = ctypes.cast(lparam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                vk = info.vkCode
                alt = bool(user32.GetAsyncKeyState(VK_MENU) & 0x8000)
                ctrl = bool(user32.GetAsyncKeyState(VK_CONTROL) & 0x8000)
                win = bool(user32.GetAsyncKeyState(VK_LWIN) & 0x8000) or bool(user32.GetAsyncKeyState(VK_RWIN) & 0x8000)

                # Bloqueos generales: con la tecla Windows bloqueada se cubren Win+Tab,
                # Win+Ctrl+D (crear escritorio) y Win+Ctrl+flechas (cambiar escritorio).
                desktop_combo = win and ctrl and vk in (VK_D, VK_LEFT, VK_RIGHT)
                blocked = (
                    vk in (VK_LWIN, VK_RWIN)
                    or desktop_combo
                    or (alt and vk in (VK_TAB, VK_ESCAPE))
                    or (ctrl and vk == VK_ESCAPE)
                )
                if blocked:
                    return 1
            return user32.CallNextHookEx(self.hook, code, wparam, lparam)

        self.callback = LowLevelProc(keyboard_proc)
        self.hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self.callback, kernel32.GetModuleHandleW(None), 0)
        return bool(self.hook)

    def uninstall(self) -> None:
        if self.hook and sys.platform == "win32":
            ctypes.windll.user32.UnhookWindowsHookEx(self.hook)
        self.hook = None
        self.callback = None
