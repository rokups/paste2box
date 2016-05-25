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
import sys

from PySide.QtGui import QDialog, QDialogButtonBox

from libp2b import const
from libp2b.settings import settings
from .ui.settings_ui import Ui_SettingsDialog

if os.name == 'nt':
    import winreg


class SettingsDialog(QDialog, Ui_SettingsDialog):
    _windows_run_reg_key = r'Software\Microsoft\Windows\CurrentVersion\Run'
    _linux_autostart_file = os.path.join(settings.config_dir, 'autostart', const.APP_NAME + '.desktop')

    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.hotkey_screen.setText(settings['hotkey/screenshot'])
        self.hotkey_clip.setText(settings['hotkey/clipboard'])
        self.autostart.setChecked(self.is_autostart_enabled())
        self.buttons.clicked.connect(self.save_or_close)
        if os.name == 'nt':
            # Windows hijacks PrintScreen button for it's screenshotting functionality therefore hotkey widget can not
            # capture this key. We must bind it manually.
            self.printscreen.setChecked(self.hotkey_screen.text() == 'Print')
            self.hotkey_screen.setEnabled(not self.printscreen.isChecked())
            self.printscreen.toggled.connect(self._windows_print_screen)
            self.clear_hotkey_screen.pressed.connect(lambda: self.printscreen.setChecked(False))
        else:
            self.printscreen.setVisible(False)
        self.resize(self.width(), 0)

    def _windows_print_screen(self, on):
        self.hotkey_screen.setEnabled(not on)
        self.hotkey_screen.setText('Print' if on else '')

    def is_autostart_enabled(self):
        if os.name == 'nt':
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._windows_run_reg_key, 0, winreg.KEY_ALL_ACCESS) as key:
                try:
                    reg_value, reg_type = winreg.QueryValueEx(key, const.APP_NAME)
                    if reg_type == winreg.REG_SZ and reg_value == self._get_executable_path():
                        return True
                    else:
                        try:
                            winreg.DeleteValue(key, self.WIN_REG_AUTORUN_KEY)
                        except OSError:
                            pass        # key does not exist
                except:
                    return False
        else:
            return os.path.exists(self._linux_autostart_file)

    def save_or_close(self, btn):
        if self.buttons.standardButton(btn) == QDialogButtonBox.Save:
            if os.name == 'nt':
                self._save_autostart_win(self.autostart.isChecked())
            else:
                self._save_autostart_linux(self.autostart.isChecked())

            settings['hotkey/screenshot'] = self.hotkey_screen.text()
            settings['hotkey/clipboard'] = self.hotkey_clip.text()
            settings.save()

            self.accept()
        else:
            self.reject()

    def _save_autostart_win(self, on):
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._windows_run_reg_key, 0, winreg.KEY_ALL_ACCESS) as key:
            if on:
                winreg.SetValueEx(key, const.APP_NAME, 0, winreg.REG_SZ, self._get_executable_path())
            else:
                try:
                    winreg.DeleteValue(key, const.APP_NAME)
                except OSError:
                    pass        # key does not exist

    def _save_autostart_linux(self, on):
        if on:
            template = \
                "[Desktop Entry]\n" \
                "Exec={executable}\n" \
                "StartupNotify=false\n" \
                "Terminal=false\n" \
                "Type=Application\n"
            with open(self._linux_autostart_file, 'w+') as fp:
                fp.write(template.format(executable=self._get_executable_path()))
        else:
            if os.path.exists(self._linux_autostart_file):
                os.unlink(self._linux_autostart_file)

    @staticmethod
    def _get_executable_path():
        if getattr(sys, 'frozen', False):
            return sys.executable
        else:
            return '{sys.executable} "{sys.argv[0]}"'.format(sys=sys)
