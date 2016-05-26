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
import urllib.parse

from PySide.QtCore import Qt
from PySide.QtGui import QLineEdit, QPlainTextEdit, QLabel, QCheckBox, QFontMetrics


def get_control_by_type(param):
    if isinstance(param, tuple):
        options = param[1:]
        param = param[0]
    else:
        options = ()

    if param == 'str':
        result = QLineEdit()
        if 'pwd' in options:
            result.setEchoMode(QLineEdit.Password)

        if 'optional' in options:
            result.setPlaceholderText('(Optional)')
    elif param == 'big_str':
        result = QPlainTextEdit()
    elif param == 'label':
        result = QLabel()
        if 'url' in options:
            result.setTextFormat(Qt.RichText)
            result.setTextInteractionFlags(Qt.TextBrowserInteraction)
            result.setOpenExternalLinks(True)
    elif param == 'checkbox':
        result = QCheckBox()
    else:
        raise RuntimeError()

    return result


def get_widget_value(widget):
    if isinstance(widget, QLineEdit):
        return widget.text()
    elif isinstance(widget, QPlainTextEdit):
        return widget.toPlainText()
    elif isinstance(widget, QLabel):
        return widget.text()
    elif isinstance(widget, QCheckBox):
        return widget.isChecked()
    else:
        raise RuntimeError()


def set_widget_value(widget, value):
    if isinstance(widget, QLineEdit):
        widget.setText(value)
    elif isinstance(widget, QPlainTextEdit):
        return widget.setPlainText(value)
    elif isinstance(widget, QLabel):
        if widget.openExternalLinks():
            widget.setToolTip(value)
            metrics = QFontMetrics(widget.font())
            display = metrics.elidedText(value, Qt.ElideRight, widget.width())
            value = urllib.parse.unquote(value)     # Because setText() escapes percent-encoded values and corrupts them
            value = '<a href="{value}">{display}</a>'.format(**locals())
        widget.setText(value)
    elif isinstance(widget, QCheckBox):
        return widget.setChecked(value not in (False, '0', '', 'False'))
    else:
        raise RuntimeError()

