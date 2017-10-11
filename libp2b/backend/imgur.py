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
from collections import OrderedDict
from imgurpython import ImgurClient

from .interface import BackendInterface as Bi


def upload_contents(self, contents, config=None, anon=True):
    if not config:
        config = {}
    b64 = base64.b64encode(contents)
    data = {'image': b64, 'type': 'base64'}
    data.update({meta: config[meta] for meta in set(self.allowed_image_fields).intersection(config.keys())})
    return self.make_request('POST', 'upload', data, anon)


class ImgurBackend(Bi):
    name = 'imgur'

    capabilities = Bi.CanPostImage | Bi.CanAuthenticate | Bi.CanAnonymous
    post_fields = OrderedDict((
        ('Filename', 'str'),
        ('Title', ('str', 'optional')),
        ('Description', ('big_str', 'optional')),
    ))
    result_fields = OrderedDict((
        ('View', 'str'),
        ('Delete', 'str'),
    ))
    login_fields = OrderedDict((
        ('Login URL', ('label', 'url')),
        ('Title', 'str'),
        ('Pin', 'str'),
    ))

    CLIENT_ID = '67057cf828a68eb'
    CLIENT_SECRET = 'e85c14fa2a4e0895a021efd5c314a95c3d4f32fb'

    def __init__(self):
        super().__init__()
        self._login_client = None

    def create(self, parameters):
        assert self.share_type == Bi.Image

        if self.progress_callback:
            self.progress_callback(-1)

        client = ImgurClient(self.CLIENT_ID, self.CLIENT_SECRET)
        if self.login:
            client.set_user_auth(self.config['login'][self.login]['access_token'],
                                 self.config['login'][self.login]['refresh_token'])

        image = upload_contents(client, self.content, {
            'name': parameters['Filename'],
            'title': parameters['Title'],
            'description': parameters['Description']
        }, self.login is None)

        ro_url = image['link'][:image['link'].rindex('.')]
        rw_url = 'https://imgur.com/delete/' + image['deletehash']

        if self.progress_callback:
            self.progress_callback(100)

        return {'View': ro_url, 'Delete': rw_url}

    def add_login_begin(self):
        self._login_client = ImgurClient(self.CLIENT_ID, self.CLIENT_SECRET)
        return {'Login URL': self._login_client.get_auth_url('pin')}

    def add_login(self, login_parameters):
        try:
            title = login_parameters['Title']
            pin = login_parameters['Pin']

            if not title or not pin:
                raise ValueError('Invalid parameters')

            if title in self.config['login']:
                raise ValueError('Login "{}" already exists.'.format(title))

            client = self._login_client
            credentials = client.authorize(pin, 'pin')
            self.config['login'][title] = {
                'access_token': credentials['access_token'],
                'refresh_token': credentials['refresh_token']
            }
            return title
        finally:
            self._login_client = None
