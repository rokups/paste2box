# paste2box - file sharing client
# Copyright (C) 2016  Rokas Kupstys
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from ctypes import windll, cast, c_void_p, c_char_p, byref, c_size_t
from ctypes.wintypes import DWORD
import struct


PAGE_EXECUTE_READWRITE = 0x40


def hotpatch(source, destination):
    source = cast(source, c_void_p).value
    destination = cast(destination, c_void_p).value
    old = DWORD()
    if windll.kernel32.VirtualProtect(source - 5, 8, PAGE_EXECUTE_READWRITE, byref(old)):
        try:
            written = c_size_t()
            jmp_code = struct.pack('<BI', 0xE9, (destination - source) & 0xFFFFFFFF)
            windll.kernel32.WriteProcessMemory(-1, source - 5, cast(jmp_code, c_char_p), len(jmp_code), byref(written))
            windll.kernel32.WriteProcessMemory(-1, source, cast(struct.pack('<H', 0xF9EB), c_char_p), 2, byref(written))
        finally:
            windll.kernel32.VirtualProtect(source - 5, 8, old, byref(old))
    return source + 2


def unhotpatch(source):
    source = cast(source, c_void_p).value
    old = DWORD()
    if windll.kernel32.VirtualProtect(source, 2, PAGE_EXECUTE_READWRITE, byref(old)):
        try:
            written = c_size_t()
            windll.kernel32.WriteProcessMemory(-1, source, cast(b'\x8B\xFF', c_char_p), 2, byref(written))
        finally:
            windll.kernel32.VirtualProtect(source, 2, old, byref(old))


if __name__ == '__main__':
    from ctypes import WINFUNCTYPE
    from ctypes.wintypes import HWND, UINT
    MessageBoxAType = WINFUNCTYPE(None, HWND, c_char_p, c_char_p, UINT)
    MessageBoxAOriginal = None

    def MessageBoxAHook(hwnd, msg, title, kind):
        hooked_title = c_char_p(b'Hooked')
        MessageBoxAOriginal(hwnd, msg, hooked_title, kind)

    MessageBoxAOriginal = MessageBoxAType(hotpatch(windll.user32.MessageBoxA, MessageBoxAType(MessageBoxAHook)))
    msg = c_char_p(b'Hello ctypes')
    title = c_char_p(b'Not hooked')
    windll.user32.MessageBoxA(None, msg, title, 0)
