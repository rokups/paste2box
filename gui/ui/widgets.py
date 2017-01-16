# paste2box - internet-enabled clipboard
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
from AnyQt.QtCore import Qt
from AnyQt.QtGui import QKeySequence
from AnyQt.QtWidgets import QLineEdit


class KeyShortcutEdit(QLineEdit):
    special_key_whitelist = [
        Qt.Key_Print,
        Qt.Key_ScrollLock,
        Qt.Key_Pause,
    ]

    special_key_with_modifiers = [
        Qt.Key_Tab,
        Qt.Key_CapsLock,
        Qt.Key_Escape,
        Qt.Key_Backspace,
        Qt.Key_Insert,
        Qt.Key_Delete,
        Qt.Key_Home,
        Qt.Key_End,
        Qt.Key_PageUp,
        Qt.Key_PageDown,
        Qt.Key_NumLock,
        Qt.UpArrow,
        Qt.RightArrow,
        Qt.DownArrow,
        Qt.LeftArrow,
    ]

    def __init__(self, *args, **kwargs):
        QLineEdit.__init__(self, *args, **kwargs)

    def keyPressEvent(self, e):
        key = e.key()
        if key in (Qt.Key_unknown, Qt.Key_Shift, Qt.Key_Control, Qt.Key_Alt, Qt.Key_Meta):
            return

        key_sequence = 0
        mod = e.modifiers()
        if mod & Qt.ShiftModifier:
            key_sequence |= int(Qt.SHIFT)
        if mod & Qt.ControlModifier:
            key_sequence |= int(Qt.CTRL)
        if mod & Qt.AltModifier:
            key_sequence |= int(Qt.ALT)

        if key in self.special_key_with_modifiers and not mod:
            return

        if e.text() == '' and key not in self.special_key_whitelist:    # Empty means a special key like F5, Delete, etc
            return

        key_sequence |= int(key)
        self.setText(QKeySequence(key_sequence).toString(QKeySequence.NativeText))


for i in range(1, 36):
    KeyShortcutEdit.special_key_whitelist.append(getattr(Qt, 'Key_F{:d}'.format(i)))
