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
from PyQt4.QtCore import QThreadPool, Qt
from PyQt4.QtGui import QDialog, QMessageBox, QLabel

from gui.ui.common import get_control_by_type, get_widget_value, set_widget_value
from .async import AsyncUploader
from libp2b.settings import settings
from .ui.login_ui import Ui_LoginDialog


class LoginDialog(QDialog, Ui_LoginDialog):
    def __init__(self, backend, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._backend = backend
        self.new_login = ''
        self.buttons.accepted.connect(self.do_login)
        self.buttons.rejected.connect(self.reject)
        self._widgets = {}

        for title, kind in backend.login_fields.items():
            label = QLabel(title)
            widget = get_control_by_type(kind)
            self._widgets[title] = widget
            self.controls.addRow(label, widget)

        for title, value in self._backend.add_login_begin().items():
            set_widget_value(self._widgets[title], value)

        self.resize(self.width(), 0)

    def do_login(self):
        self.buttons.setEnabled(False)
        parameters = {name: get_widget_value(widget) for name, widget in self._widgets.items()}
        logger_in = AsyncUploader(self._backend.add_login, parameters)
        logger_in.signals.success.connect(self.on_success)
        logger_in.signals.error.connect(self.on_error)
        QThreadPool.globalInstance().start(logger_in)

    def on_success(self, new_login):
        settings.save()
        self.new_login = new_login
        self.accept()

    def on_error(self, error):
        QMessageBox.warning(self, self.tr('Warning'), error)
        self.reject()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
