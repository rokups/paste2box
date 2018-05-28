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
import sys

import json
import httplib2
import os
from io import BytesIO
from collections import OrderedDict
from googleapiclient import discovery
from googleapiclient.http import MediaIoBaseUpload
from libp2b import const
from oauth2client import client, file

from .interface import BackendInterface as Bi


class MemoryStorage(file.BaseStorage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._data = None

    def locked_get(self):
        return self._data

    def locked_put(self, credentials):
        self._data = credentials

    def locked_delete(self):
        self._data = None


class GoogleDriveBackend(Bi):
    name = 'gdrive'
    capabilities = Bi.CanPostImage | Bi.CanPostText | Bi.CanPostFile | Bi.CanAuthenticate
    post_fields = OrderedDict((
        ('Filename', 'str'),
        ('Title', ('str', 'optional')),
        ('Description', ('big_str', 'optional')),
    ))
    result_fields = OrderedDict((
        ('View', 'str'),
        ('Direct', 'str'),
    ))
    login_fields = OrderedDict((
        ('Login URL', ('label', 'url')),
        ('Title', 'str'),
        ('Code', 'str'),
    ))

    def __init__(self):
        super().__init__()
        self._flow = None

    def create(self, parameters):
        super().create(parameters)

        if self.progress_callback:
            self.progress_callback(-1)

        credentials = client.OAuth2Credentials.from_json(json.dumps(self.config['login'][self.login]))
        store = MemoryStorage()
        store.put(credentials)
        credentials.set_store(store)

        http = credentials.authorize(httplib2.Http())
        service = discovery.build('drive', 'v3', http=http)

        fd = None
        try:
            mime = 'application/octet-stream'
            if self.share_type == Bi.File:
                assert isinstance(self.content, str)
                fd = open(self.content, 'rb')
            elif self.share_type == Bi.Text:
                assert isinstance(self.content, str)
                fd = BytesIO(self.content.encode('utf-8'))
                mime = 'text/plain'
            elif isinstance(self.content, bytes):
                fd = BytesIO(self.content)
            else:
                raise RuntimeError()

            media_body = MediaIoBaseUpload(fd, mimetype=mime)
            body = {
                'name': parameters['Title'] or parameters['Filename'],
                'originalFilename': parameters['Filename'],
                'description': parameters['Description'],
                'mimeType': mime,
            }
            metadata = service.files().create(body=body, media_body=media_body).execute()

        except Exception:
            if self.progress_callback:
                self.progress_callback(0)
            raise
        else:
            if self.progress_callback:
                self.progress_callback(100)
            return {
                'View': 'https://drive.google.com/file/d/{}/view?usp=sharing'.format(metadata['id']),
                'Direct': 'https://drive.google.com/uc?id={}'.format(metadata['id']),
            }
        finally:
            if fd:
                fd.close()

    def add_login_begin(self):
        gdrive = 'googledrive.json'
        if not getattr(sys, 'frozen', False):
            parent_dir = os.path.realpath(__file__)
            while True:
                assert len(parent_dir) > (3 if os.name == 'nt' else 1)
                gdrive = os.path.join(parent_dir, 'googledrive.json')
                if os.path.isfile(gdrive):
                    break
                else:
                    parent_dir = os.path.dirname(parent_dir)

        flow = self._flow = client.flow_from_clientsecrets(gdrive, 'https://www.googleapis.com/auth/drive.file')
        flow.user_agent = const.APP_USERAGENT
        flow.redirect_uri = client.OOB_CALLBACK_URN
        authorize_url = flow.step1_get_authorize_url()
        return {'Login URL': authorize_url}

    def add_login(self, login_parameters):
        try:
            title = login_parameters['Title']
            code = login_parameters['Code']

            if not title or not code:
                raise ValueError('Invalid parameters')

            if title in self.config['login']:
                raise ValueError('Login "{}" already exists.'.format(title))

            try:
                credentials = self._flow.step2_exchange(code, http=None)
            except client.FlowExchangeError as e:
                raise ValueError('Authentication has failed: {}'.format(str(e)))

            self.config['login'][title] = json.loads(credentials.to_json())
            return title
        finally:
            self._flow = None
