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
import base64
import json
from collections import OrderedDict
from datetime import datetime
from urllib.error import HTTPError
from urllib.request import urlopen, Request

from .interface import BackendInterface as Bi


class GistBackend(Bi):
    name = 'gist'

    capabilities = Bi.CanPostText | Bi.CanAuthenticate | Bi.CanAnonymous
    post_fields = OrderedDict((
        ('Filename', 'str'),
        ('Description', ('big_str', 'optional')),
        ('Public', 'checkbox'),
    ))
    result_fields = OrderedDict((
        ('View', 'str'),
    ))
    login_fields = OrderedDict((
        ('Username', 'str'),
        ('Password', ('str', 'pwd')),
    ))

    def __init__(self):
        super().__init__()
        self._headers = {
            'Accept-Encoding': 'identity, deflate, compress, gzip',
            'User-Agent': 'paste2box/1.0',
            'Accept': 'application/vnd.github.v3.base64',
        }

    def create(self, parameters):
        assert self.share_type == Bi.Text

        if self.progress_callback:
            self.progress_callback(-1)

        req = {
            'description': parameters['Description'],
            'public': parameters['Public'],
            'files': {
                parameters['Filename']: {
                    'content': self.content
                }
            }
        }

        url = 'https://api.github.com/gists'
        if self.login:
            url += '?access_token=' + self.config['login'][self.login]['token']

        res = json.loads(urlopen(url, json.dumps(req).encode()).read().decode())

        if self.progress_callback:
            self.progress_callback(100)

        return {'View': res['html_url']}

    def add_login(self, login_parameters):
        try:
            username = login_parameters['Username']
            password = login_parameters['Password']

            if not username or not password:
                raise ValueError('Invalid parameters')

            if username in self.config['login']:
                raise ValueError('Login "{}" already exists.'.format(username))

            req = Request('https://api.github.com/authorizations')
            req.add_header('Authorization',
                           'Basic ' + base64.b64encode('{}:{}'.format(username, password).encode()).decode())
            response = json.loads(urlopen(req, json.dumps({
                'scopes': ['gist'],
                'note': 'paste2box ({})'.format(datetime.now().isoformat(' '))
            }).encode()).read().decode())
        except HTTPError as e:
            if e.code == 401:
                raise Exception('Incorrect username or password')
            else:
                response = json.loads(e.fp.read().decode())
                if response['errors']['code'] == 'already_exists':
                    raise Exception('Authorization already exists')
                else:
                    raise Exception('Unknown error')
        else:
            self.config['login'][username] = {'id': response['id'], 'token': response['token']}
            return username
