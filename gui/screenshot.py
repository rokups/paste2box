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
from PySide.QtCore import Qt, QEvent, QRect
from PySide.QtGui import QApplication, QDialog, QPixmap, QRubberBand, QPushButton, QHBoxLayout, QWidget, QMessageBox,\
    QFileDialog, QPainter, QColor


RESIZE_TOP = 1
RESIZE_RIGHT = 2
RESIZE_BOTTOM = 4
RESIZE_LEFT = 8
RESIZE_DRAG = 15


class Screenshot(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent, Qt.CustomizeWindowHint | Qt.FramelessWindowHint | Qt.Window |
                         Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.installEventFilter(self)
        self.setMouseTracking(True)
        self._band = QRubberBand(QRubberBand.Rectangle, self)

        self._resize_origin = None
        self._drag_mask = 0
        self._origin = None
        self.selected_image = None

        desktop = QApplication.desktop()
        self.setGeometry(desktop.geometry())

        # Window background
        self._snapshot = QPixmap.grabWindow(desktop.winId(), 0, 0, desktop.width(), desktop.height())

        self._image = self._snapshot.toImage()
        self._transparent = self._image.copy()
        self.set_alpha(self._transparent, 100)

        # Buttons
        self._buttons = QWidget(self)
        self._button_layout = QHBoxLayout(self._buttons)
        self._button_layout.setSpacing(0)
        self._button_layout.setContentsMargins(0, 0, 0, 0)
        self._button_layout.setContentsMargins(0, 0, 0, 0)
        self.save_as = QPushButton(self.tr('Save As'))
        self.save_as.pressed.connect(self.save_image_as)
        self.save_as.setCursor(Qt.ArrowCursor)
        self._button_layout.addWidget(self.save_as)
        self.copy = QPushButton(self.tr('Copy'))
        self.copy.pressed.connect(self.copy_to_clipboard)
        self.copy.setCursor(Qt.ArrowCursor)
        self._button_layout.addWidget(self.copy)
        self.share = QPushButton(self.tr('Share'))
        self.share.pressed.connect(self.share_selection)
        self.share.setCursor(Qt.ArrowCursor)
        self._button_layout.addWidget(self.share)
        self._buttons.hide()

    @staticmethod
    def set_alpha(pixmap, val):
        alpha = pixmap.copy()
        painter = QPainter(alpha)
        painter.fillRect(alpha.rect(), QColor(val, val, val))
        painter.end()
        pixmap.setAlphaChannel(alpha)
        return pixmap

    def paintEvent(self, _):
        painter = QPainter(self)
        painter.fillRect(self._transparent.rect(), Qt.black)
        painter.drawImage(0, 0, self._transparent)
        if self._band.isVisible():
            br = self._band.geometry()
            r = QRect(br.topLeft(), br.bottomRight())
            painter.drawImage(r, self._image.copy(r))

    def get_selection(self):
        return self._snapshot.copy(self._band.geometry())

    def save_image_as(self):
        img = self.get_selection().toImage()
        if img.isNull():
            QMessageBox.critical(self, self.tr('Error'), self.tr('No image was selected!'))
            return

        self.hide()

        formats = {
            self.tr('Portable Network Graphics (*.png)'): 'png',
            self.tr('Joint Photographic Experts Group (*.jpg)'): 'jpg',
            self.tr('Graphics Interchange Format (*.gif)'): 'gif',
            self.tr('Bitmap (*.bmp)'): 'bmp',
            self.tr('All Images (*.png *.jpg *.gif *.bmp)'): 'all'
        }

        destination, file_format = QFileDialog.getSaveFileName(self, 'Save image', '', ';;'.join(formats.keys()))
        if destination:
            try:
                file_format = formats[file_format]
            except KeyError:
                file_format = 'png'
            if file_format == 'all':
                file_format = 'png'
            if not destination.lower().endswith('.' + file_format):
                destination += '.' + file_format
            img.save(destination, file_format, 0 if file_format == 'png' else 90)
        self.reject()

    def copy_to_clipboard(self):
        img = self.get_selection()
        if img.isNull():
            QMessageBox.critical(self, self.tr('Error'), self.tr('No image was selected!'))
            return
        QApplication.clipboard().setPixmap(img)
        self.reject()

    def share_selection(self):
        self.selected_image = self.get_selection()
        self.accept()

    def eventFilter(self, obj, e):
        if e.type() == QEvent.Enter:
            self.activateWindow()
        if e.type() == QEvent.KeyPress and e.key() == Qt.Key_Escape:
            self.reject()
            return True
        return super().eventFilter(obj, e)

    def mousePressEvent(self, event):
        if self.update_cursor_shape(event.pos(), event.button() == Qt.LeftButton):
            self._resize_origin = event.pos()
        else:
            self._origin = event.pos()
            if not self._band.isVisible():
                self._band.setGeometry(QRect(self._origin, self._origin))
                self._band.show()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        p = event.pos()
        mouse_down = event.buttons() & Qt.LeftButton
        if mouse_down:
            m = self._drag_mask
            wr = self.rect()
            if m:
                g = self._band.geometry()
                d = p - self._resize_origin
                if d.x() or d.y():
                    if m == RESIZE_DRAG:
                        g.translate(d)
                    else:
                        if m & RESIZE_LEFT:
                            g.translate(d.x(), 0)
                            g.setWidth(g.width() - d.x())
                        elif m & RESIZE_RIGHT:
                            g.setWidth(g.width() + d.x())
                        if m & RESIZE_TOP:
                            g.translate(0, d.y())
                            g.setHeight(g.height() - d.y())
                        elif m & RESIZE_BOTTOM:
                            g.setHeight(g.height() + d.y())
                    self._resize_origin = p
                    # Contain in the screen
                    px = min(max(g.topLeft().x(), 0), wr.width() - g.width())
                    py = min(max(g.topLeft().y(), 0), wr.height() - g.height())
                    g.moveTo(px, py)
            else:
                g = QRect(self._origin, p).normalized()
            self._band.setGeometry(g)
            br = self._band.geometry()
            x = (br.width() / 2 - self._buttons.width() / 2) + br.left()    # buttons at center of band
            x = max(0, min(x, wr.width() - self._buttons.width()))          # prevent going off-screen
            if (wr.height() - br.bottom()) > self._buttons.height():        # if at bottom
                y = br.bottom()
            else:
                y = br.top() - self._buttons.height()
            self._buttons.move(x, y)
            self._buttons.show()
            self.repaint()
        else:
            self.update_cursor_shape(p, mouse_down)
            self._drag_mask = self.get_drag_mask(p)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.update_cursor_shape(event.pos(), False)
        super().mouseReleaseEvent(event)

    def update_cursor_shape(self, p, mouse_down):
        m = self.get_drag_mask(p)
        if m == RESIZE_DRAG:
            self.setCursor(Qt.ClosedHandCursor if mouse_down else Qt.OpenHandCursor)
        elif (m & RESIZE_LEFT and m & RESIZE_TOP) or (m & RESIZE_RIGHT and m & RESIZE_BOTTOM):
            self.setCursor(Qt.SizeFDiagCursor)
        elif (m & RESIZE_LEFT and m & RESIZE_BOTTOM) or (m & RESIZE_RIGHT and m & RESIZE_TOP):
            self.setCursor(Qt.SizeBDiagCursor)
        elif m & RESIZE_LEFT or m & RESIZE_RIGHT:
            self.setCursor(Qt.SizeHorCursor)
        elif m & RESIZE_TOP or m & RESIZE_BOTTOM:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
            return False
        return True

    def get_drag_mask(self, p):
        br = self._band.geometry()
        if br.contains(p):
            def is_hovering(x):
                return 0 <= x <= 10
            m = 0
            m |= RESIZE_LEFT if is_hovering(p.x() - br.left()) else 0
            m |= RESIZE_RIGHT if is_hovering(br.right() - p.x()) else 0
            m |= RESIZE_BOTTOM if is_hovering(br.bottom() - p.y()) else 0
            m |= RESIZE_TOP if is_hovering(p.y() - br.top()) else 0
            if m:
                return m
            return RESIZE_DRAG
        return 0
