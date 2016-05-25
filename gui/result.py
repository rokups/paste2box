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
from PySide.QtCore import QThreadPool, QUrl, Qt
from PySide.QtGui import QDialog, QMessageBox, QApplication, QDesktopServices, QLabel, QPushButton

from gui.ui.common import get_control_by_type, get_widget_value, set_widget_value
from .async import AsyncUploader
from libp2b.settings import settings
from .ui.result_ui import Ui_ResultDialog


class ResultDialog(QDialog, Ui_ResultDialog):
    def __init__(self, backend, parameters, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._backend = backend
        self._parameters = parameters
        self._widgets = {}

        self._progress(-1)

        for row, (title, kind) in enumerate(backend.result_fields.items()):
            label = QLabel(title)
            self.controls.addWidget(label, row, 0)

            widget = get_control_by_type(kind)
            widget.setEnabled(False)
            self.controls.addWidget(widget, row, 1)

            copy_button = QPushButton(self.tr('Copy'))
            copy_button.pressed.connect(lambda w=widget: self.copy_text(w))
            copy_button.setEnabled(False)
            self.controls.addWidget(copy_button, row, 2)

            open_button = QPushButton(self.tr('Open'))
            open_button.pressed.connect(lambda w=widget: self.open_url(w))
            open_button.setEnabled(False)
            self.controls.addWidget(open_button, row, 3)

            self._widgets[title] = (widget, copy_button, open_button)

        self.auto_close.stateChanged.connect(self.save_auto_close)
        try:
            self.auto_close.setChecked(settings['auto_close'])
        except (KeyError, TypeError):
            pass

        self.resize(self.width(), 0)
        uploader = AsyncUploader(self._backend.create, parameters)
        uploader.signals.success.connect(self.on_success)
        uploader.signals.error.connect(self.on_error)
        QThreadPool.globalInstance().start(uploader)

    def save_auto_close(self):
        settings['auto_close'] = self.auto_close.isChecked()
        settings.save()

    def _progress(self, percent):
        if percent == -1:
            self.progress.setMaximum(0)
            self.progress.setValue(0)
        else:
            self.progress.setMaximum(100)
            self.progress.setValue(percent)

    def on_success(self, result):
        self._progress(100)

        for title, (widget, copy_button, open_button) in self._widgets.items():
            widget.setEnabled(True)
            copy_button.setEnabled(True)
            open_button.setEnabled(True)
            set_widget_value(widget, result[title])

    def on_error(self, error):
        self._progress(0)
        QMessageBox.critical(self, self.tr('Error'), error)
        self.reject()

    def copy_text(self, widget):
        QApplication.clipboard().setText(get_widget_value(widget))
        if self.auto_close.isChecked():
            self.accept()

    def open_url(self, widget):
        QDesktopServices.openUrl(QUrl(get_widget_value(widget)))
        if self.auto_close.isChecked():
            self.accept()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()
