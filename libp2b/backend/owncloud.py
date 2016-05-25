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
from collections import OrderedDict
from owncloud.owncloud import Client, HTTPResponseError

from .interface import BackendInterface as Bi


class OwnCloudBackend(Bi):
    name = 'owncloud'
    capabilities = Bi.CanPostImage | Bi.CanPostText | Bi.CanPostFile | Bi.CanAuthenticate
    post_fields = OrderedDict((
        ('Filename', 'str'),
        ('Password', ('str', 'pwd', 'optional')),
    ))
    result_fields = OrderedDict((
        ('View', 'str'),
    ))
    login_fields = OrderedDict((
        ('Server URL', 'str'),
        ('Login', 'str'),
        ('Password', ('str', 'pwd')),
    ))

    def __init__(self):
        super().__init__()

    def create(self, parameters):
        super().create(parameters)

        if self.progress_callback:
            self.progress_callback(-1)

        client = Client(self.config['login'][self.login]['url'])
        client.login(self.config['login'][self.login]['username'],
                     self.config['login'][self.login]['password'])

        target_path = 'paste2box/' + parameters['Filename']

        if self.share_type == Bi.File and isinstance(self.content, str):
            content = self.content
            upload_func = client.put_file
        else:
            assert isinstance(self.content, bytes)
            content = self.content
            upload_func = client.put_file_contents

        try:
            upload_func(target_path, content)
        except HTTPResponseError:
            client.mkdir('paste2box')
            upload_func(target_path, content)

        read_link = client.share_file_with_link(target_path, password=parameters['Password']).get_link()

        if self.progress_callback:
            self.progress_callback(100)

        return {'View': read_link}

    def add_login(self, login_parameters):
        username = login_parameters['Login']
        password = login_parameters['Password']
        url = login_parameters['Server URL']

        if not username or not password or not url:
            raise ValueError('Invalid parameters')

        if username in self.config['login']:
            raise ValueError('Login "{}" already exists.'.format(username))

        client = Client(url)
        try:
            client.login(username, password)
        except HTTPResponseError as e:
            if e.status_code == 401:
                raise ValueError('Invalid username or password')
        else:
            self.config['login'][username] = {
                'username': username,
                'password': password,
                'url': url
            }
            return username
