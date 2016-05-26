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

APP_NAME = 'paste2box'
APP_VERSION = (0, 1, 1)
APP_VERSION_STR = '.'.join(str(v) for v in APP_VERSION)
APP_USERAGENT = APP_NAME + '/' + APP_VERSION_STR

BIG_FILE_WARNING_SIZE = 10 * 1024 * 1024
