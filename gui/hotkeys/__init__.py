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
import os


def initialize():
    if os.name == 'nt':
        from gui.hotkeys.win32.global_hotkey_win import GlobalHotkeyManagerWin
        return GlobalHotkeyManagerWin()
    elif os.name == 'posix':
        from gui.hotkeys.x11.global_hotkey_x11 import GlobalHotkeyManagerX11
        return GlobalHotkeyManagerX11()
