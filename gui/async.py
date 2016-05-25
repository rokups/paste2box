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
import traceback

import requests
from PySide.QtCore import QObject, QRunnable, Signal


class AsyncUploaderSignals(QObject):
    success = Signal(object)
    error = Signal(str)

    def __init__(self):
        super().__init__()


class AsyncUploader(QRunnable):
    def __init__(self, callable_, parameters):
        super().__init__()
        self.signals = AsyncUploaderSignals()
        self._callable = callable_
        self._parameters = parameters
        self.setAutoDelete(True)

    def run(self):
        try:
            results = self._callable(self._parameters)
            if results:
                self.signals.success.emit(results)
            else:
                self.signals.error.emit('Unknown error')
        except requests.ConnectionError:
            self.signals.error.emit(self.signals.tr('Could not connect to server. Try again later.'))
        except Exception as e:
            self.signals.error.emit(str(e) + '\n' + traceback.format_exc())
