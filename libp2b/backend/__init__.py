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
from collections import OrderedDict

from .interface import BackendInterface
from .imgur import ImgurBackend
from .gist import GistBackend
from .owncloud import OwnCloudBackend
from .googledrive import GoogleDriveBackend

all_backends = OrderedDict((
    (b.name, b) for b in [OwnCloudBackend, ImgurBackend, GistBackend, GoogleDriveBackend]
))
