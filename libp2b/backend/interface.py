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
from libp2b.settings import settings


class BackendInterface(object):
    name = None
    destination = None
    capabilities = 0
    default_config = {}
    CanPostText = 1
    CanPostImage = 1 << 1
    CanPostFile = 1 << 2
    CanAuthenticate = 1 << 3
    CanAnonymous = 1 << 4

    Image = 1
    Text = 2
    File = 3

    def __init__(self):
        name = self.name
        if name not in settings:
            settings[name] = self.default_config
        self.config = settings[name]
        if self.capabilities & self.CanAuthenticate:
            if 'login' not in self.config:
                self.config['login'] = {}
        self.content = None
        self.login = None
        self.progress_callback = None
        self.share_type = None

    def create(self, parameters):
        if not (self.capabilities & self.CanAnonymous) and not self.login:
            raise ValueError('Login required')
        if not (self.capabilities & self.CanAuthenticate) and self.login:
            raise ValueError('Login not possible')

    def add_login(self, login_parameters):
        raise NotImplemented()

    def add_login_begin(self):
        return {}
