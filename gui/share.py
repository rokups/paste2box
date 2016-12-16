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
from time import time

from PyQt4.QtCore import Qt, QBuffer, QTimer
from PyQt4.QtGui import QDialog, QMessageBox, QPixmap, QLabel, QImage, QWidget

from gui.login import LoginDialog
from gui.result import ResultDialog
from gui.ui.common import get_widget_value, get_control_by_type, set_widget_value
from libp2b import const
from libp2b.backend import all_backends
from libp2b.backend import BackendInterface as Bi
from libp2b.settings import settings
from libp2b.utilities import format_size, read_text_from_file, dedent_text_and_truncate, file_has_extension
from .ui.share_ui import Ui_ShareDialog


class ShareDialog(QDialog, Ui_ShareDialog):

    def __init__(self, parent=None, *, mime=None, image=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self._backend = None
        self._backend_controls = {}
        self._label_anonymous = self.tr('Anonymous')
        self._label_select_login = self.tr('Select Login')
        self._available_backends = []

        data = None
        file_name = None
        if image:
            self._share_type = Bi.Image
            data = image
        elif mime:
            if mime.hasImage():
                self._share_type = Bi.Image
                data = mime.imageData()
            elif mime.hasUrls():
                urls = mime.urls()
                if len(urls) == 1:
                    file_path = os.path.realpath(urls[0].toLocalFile())
                    if not os.path.isfile(file_path):
                        raise ValueError(self.tr('Directories can not be shared'))
                    file_size = os.path.getsize(file_path)
                    file_name = os.path.basename(file_path)

                    if file_size > const.BIG_FILE_WARNING_SIZE:
                        file_name = os.path.basename(file_path)
                        nice_size = format_size(file_size)
                        result = QMessageBox.warning(self, self.tr('Warning'),
                                                     self.tr('File "{file_name}" {nice_size}.\n'
                                                             'Are you sure you want to continue?').format(**locals()),
                                                     QMessageBox.Yes | QMessageBox.Abort)
                        if result == QMessageBox.Abort:
                            QTimer.singleShot(0, self.reject)
                            return

                    if file_has_extension(file_path, ('png', 'jpg', 'jpeg', 'bmp', 'gif')):
                        image = QPixmap(file_path)
                    else:
                        image = None
                    if not image or image.isNull():
                        data = read_text_from_file(file_path)
                        if data:
                            self._share_type = Bi.Text
                        else:
                            self._share_type = Bi.File
                            data = file_path
                    else:
                        self._share_type = Bi.Image
                        data = image
                else:
                    raise ValueError(self.tr('Can not share more than one file'))

            elif mime.hasText():
                self._share_type = Bi.Text
                data = mime.text()
        else:
            raise RuntimeError()

        if not data:
            raise ValueError(self.tr('There is no content in your clipboard.\nCopy something in order to share it.'))

        if self._share_type == Bi.Image:
            if not file_name:
                file_name = '{}-{}.png'.format('screenshot' if image else 'image', int(time()))
            if data.width() > self.image_preview.width() or data.height() > self.image_preview.height():
                preview = data.scaled(self.image_preview.size(), Qt.KeepAspectRatio)
            else:
                preview = data
            if isinstance(preview, QImage):
                preview = QPixmap.fromImage(preview)
            self.image_preview.setPixmap(preview)
            self.preview_stack.setCurrentIndex(0)
            buf = QBuffer()
            data.save(buf, 'png', 100)
            data = buf.data().data()
        elif self._share_type == Bi.Text:
            if not file_name:
                file_name = 'file-{}.txt'.format(int(time()))
            self.text_preview.setPlainText(dedent_text_and_truncate(data, 128))
            self.preview_stack.setCurrentIndex(1)
        elif self._share_type == Bi.File:
            if not file_name:
                file_name = 'file-{}.bin'.format(int(time()))
            self.text_preview.setPlainText(self.tr('No preview available'))
            self.preview_stack.setCurrentIndex(1)

        self._file_name = file_name
        self._data = data

        self.populate_backends()

        self.share.pressed.connect(self.share_item)
        self.add_login.pressed.connect(self.on_add_login)
        self.logout.pressed.connect(self.logout_selected)
        self.login_list.currentIndexChanged.connect(self.select_login)

        min_height = self.backend_selector.minimumSizeHint().height()
        if os.name == 'nt':
            # On windows tab widget and font are rather small
            min_height -= 5
            for el in (self.add_login, self.login_list, self.logout, self.share):
                font = el.font()
                font.setPointSize(12)
                el.setFont(font)
            self.login_list.setFixedHeight(self.add_login.height() - 2)
        self.backend_selector.setFixedHeight(min_height)
        self.backend_selector.currentChanged.connect(self.select_backend)
        if self.backend_selector.height() < self.add_login.height():
            # Move tab widget down based on size of controls on the right. Makes widgets below seem to belong to the
            # selected tab.
            self.backend_selector.move(0, self.add_login.height() - self.backend_selector.height())

        self.resize(self.width(), 0)
        self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
        self.raise_()
        self.activateWindow()

    def select_backend_by_name(self, name):
        for i, backend_type in enumerate(self._available_backends):
            if backend_type.name == name:
                self.backend_selector.setCurrentIndex(i)
                self.select_backend(i)
                return True
        return False

    def select_backend(self, backend_index):
        assert len(self._available_backends)
        self._backend = self._available_backends[backend_index]()

        self.populate_logins()
        self.setWindowTitle('{} {}'.format(self.tr('Share on'), self._backend.name))

        # Populate widgets
        for i in reversed(range(self.backend_controls.count())):
            self.backend_controls.itemAt(i).widget().setParent(None)

        self._backend_controls = {}
        for title, kind in self._backend.post_fields.items():
            label = QLabel(title)
            control = get_control_by_type(kind)
            self._backend_controls[title] = control
            self.backend_controls.addRow(label, control)
            if title == 'Filename':
                set_widget_value(control, self._file_name)

    def populate_backends(self):
        try:
            self.backend_selector.blockSignals(True)
            self._available_backends = []

            while self.backend_selector.count():
                self.backend_selector.removeTab(0)

            for name, backend in all_backends.items():
                if (self._share_type == Bi.Image and backend.capabilities & Bi.CanPostImage) or \
                   (self._share_type == Bi.Text and backend.capabilities & Bi.CanPostText) or \
                   (self._share_type == Bi.File and backend.capabilities & Bi.CanPostFile):
                    self.backend_selector.addTab(QWidget(), name)
                    self._available_backends.append(backend)
        finally:
            self.backend_selector.blockSignals(False)

        try:
            last_backend = settings['last_backend/{}'.format(self._share_type)]
        except KeyError:
            last_backend = list(all_backends.values())[0].name
        if not self.select_backend_by_name(last_backend):
            self.select_backend(0)

    def logout_selected(self):
        selected_login = self.get_login_name()
        if selected_login:
            del self._backend.config['login'][selected_login]
            settings.save()
            self.populate_logins()

    def on_add_login(self):
        dlg = LoginDialog(self._backend)
        dlg.show()
        if dlg.exec_() == QDialog.Accepted and dlg.new_login:
            self.populate_logins()
            self.login_list.setCurrentIndex(self.login_list.findText(dlg.new_login))

    def select_login(self, index):
        self._backend.config['last_login'] = self.get_login_name()
        settings.save()

    def populate_logins(self):
        backend = self._backend
        self.login_list.blockSignals(True)
        try:
            self.login_list.clear()
            if backend.capabilities & Bi.CanAuthenticate:
                self.login_list.setEnabled(True)
                self.logout.setEnabled(True)
                self.add_login.setEnabled(True)
                if backend.capabilities & Bi.CanAnonymous:
                    self.login_list.addItem(self._label_anonymous)
                else:
                    self.login_list.addItem(self._label_select_login)

                for login_name in self._backend.config['login'].keys():
                    self.login_list.addItem(login_name)

                try:
                    self.login_list.setCurrentIndex(max(0, self.login_list.findText(
                        self._backend.config['last_login'])))
                except KeyError:
                    pass                    # No last login saved
            else:
                self.login_list.setEnabled(False)
                self.logout.setEnabled(False)
                self.add_login.setEnabled(False)
        finally:
            self.login_list.blockSignals(False)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()

    def get_login_name(self):
        login_name = self.login_list.currentText()
        if login_name not in (self._label_select_login, self._label_anonymous):
            return login_name

    def share_item(self):
        settings['last_backend/{}'.format(self._share_type)] = self._backend.name
        settings.save()
        parameters = {title: get_widget_value(w) for title, w in self._backend_controls.items()}

        if self.login_list.isVisible():
            self._backend.login = self.get_login_name()

        self._backend.content = self._data
        self._backend.share_type = self._share_type

        self.close()

        dlg = ResultDialog(self._backend, parameters, self)
        dlg.show()
        dlg.exec_()
