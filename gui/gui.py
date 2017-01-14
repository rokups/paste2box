#!/usr/bin/env python3
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
import os
import sys
from PyQt4.QtCore import Qt, qDebug
from PyQt4.QtGui import QApplication, QDialog, QMessageBox, QMainWindow, QSystemTrayIcon, QMenu, QIcon, QCursor,\
    QKeySequence

from gui.settings import SettingsDialog
from libp2b.settings import settings
from libp2b import const
from .share import ShareDialog
from .screenshot import Screenshot
from . import hotkeys


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(':/res/box.png'))

        self._tray = QSystemTrayIcon()
        self._tray.setIcon(QIcon(':/res/box.png'))
        self._tray.activated.connect(self.show_tray_menu)
        self._tray.show()
        self._menu = None
        self._action_screen = None
        self._action_clip = None
        self._screenshot_wnd = None
        self.rebuild_menu()

        self._hotkey = hotkeys.initialize()

        if not settings['initialized']:
            settings['initialized'] = True
            settings['hotkey/screenshot'] = 'Print'
            settings['hotkey/clipboard'] = 'Ctrl+Alt+P'
            settings.save()

        self.register_hotkeys()
        self.load_settings()

    def rebuild_menu(self):
        # Terrible way to clear hotkey shortcuts set to actions because Qt can not do that.
        self._menu = QMenu()
        self._action_screen = self._menu.addAction(self.tr('Make Screenshot'))
        self._action_screen.triggered.connect(self.capture_screen)
        self._action_clip = self._menu.addAction(self.tr('Share Clipboard'))
        self._action_clip.triggered.connect(self.share_clipboard)
        self._menu.addSeparator()
        self._menu.addAction(self.tr('Settings')).triggered.connect(self.show_settings)
        self._menu.addSeparator()
        self._menu.addAction(self.tr('Exit')).triggered.connect(lambda: QApplication.exit(0))
        self._tray.setContextMenu(self._menu)

    def __del__(self):
        self._hotkey.destroy()

    def show_tray_menu(self):
        self._menu.popup(QCursor.pos())

    def capture_screen(self):
        if self._screenshot_wnd:
            return

        self._screenshot_wnd = wnd = Screenshot()
        result = wnd.exec()
        self._screenshot_wnd = None
        if result == QDialog.Accepted:
            wnd = ShareDialog(self, image=wnd.selected_image)
            wnd.show()
            wnd.exec()

    def share_clipboard(self):
        mime = QApplication.clipboard().mimeData()
        try:
            wnd = ShareDialog(self, mime=mime)
        except ValueError as e:
            QMessageBox.critical(self, self.tr('Error'), str(e))
            return
        else:
            wnd.show()
            wnd.exec()

    def load_settings(self):
        pass

    def register_hotkeys(self):
        if self._hotkey:
            self.rebuild_menu()
            self._hotkey.unregister(winid=self.winId())
            hotkey_bindings = {
                settings['hotkey/clipboard']: (self.share_clipboard, self._action_clip),
                settings['hotkey/screenshot']: (self.capture_screen, self._action_screen)
            }
            for hotkey, (callback, action) in hotkey_bindings.items():
                if hotkey:
                    if self._hotkey.register(hotkey, callback, self.winId()):
                        sequence = QKeySequence(hotkey) if hotkey else QKeySequence()
                        action.setShortcut(sequence)
                    else:
                        QMessageBox.critical(self, 'Error', 'Could not bind {} hotkey!\n'
                                                            'Key combination {} is probably already in use.'
                                             .format(const.APP_NAME, hotkey))
        else:
            qDebug('Hotkeys are not supported on this platform')

    def show_settings(self):
        self._hotkey.unregister(winid=self.winId())
        dlg = SettingsDialog(self)
        dlg.show()
        if dlg.exec_() == QDialog.Accepted:
            self.load_settings()
        self.register_hotkeys()


def main():
    if getattr(sys, 'frozen', False):
        import httplib2
        httplib2.CA_CERTS = os.environ['REQUESTS_CA_BUNDLE'] = \
            os.path.join(os.path.dirname(sys.executable), 'cacert.pem')
    QApplication.setAttribute(Qt.AA_X11InitThreads)
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.clipboard().mimeData()                  # Sometimes first try to acquire clipboard fails. So be it.
    wnd = MainWindow()
    wnd.hide()
    app.exec_()
