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
import copy
import json
import sys
import os


class SettingsManager(object):
    _defaults = {}

    def __init__(self):
        if sys.platform in ('linux', 'linux2'):
            try:
                self.config_dir = os.environ['XDG_CONFIG_HOME']
            except KeyError:
                self.config_dir = os.path.join(os.environ['HOME'], '.config')
        elif sys.platform == 'win32':
            self.config_dir = os.environ['APPDATA']
        else:
            raise NotImplementedError('Platform "{}" is not supported!'.format(sys.platform))
        self._settings_file = os.path.join(self.config_dir, 'p2b.json')
        try:
            with open(self._settings_file) as fp:
                self._settings = json.loads(fp.read())
        except (ValueError, FileNotFoundError):
            self._settings = copy.deepcopy(self._defaults)
        self._auto_save = 0

    @staticmethod
    def register_defaults(backends):
        for backend in backends:
            SettingsManager._defaults[backend.name] = backend.default_settings

    def __contains__(self, item):
        try:
            value = self[item]
            return value is not None
        except KeyError:
            return False

    def __getitem__(self, item):
        parts = item.split('/')
        s = self._settings
        d = self._defaults
        for i, p in enumerate(parts):
            if d is not None:
                try:
                    d = d[p]
                except KeyError:
                    if i == len(parts) - 1:
                        d = None
                    else:
                        d = {}
            if s is not None:
                try:
                    s = s[p]
                except KeyError:
                    s[p] = d
                    s = d
            if s is None and d is None:
                break

        if s is not None:
            return s

        if d is not None:
            return d

        return None

    def __setitem__(self, key, value):
        parts = key.split('/')
        s = self._settings
        d = self._defaults
        for i, p in enumerate(parts):
            if d is not None:
                try:
                    d = d[p]
                except KeyError:
                    d = None
            if i == (len(parts) - 1):
                s[p] = value
            else:
                try:
                    s = s[p]
                except KeyError:
                    if d is not None:
                        s[p] = d
                    else:
                        s[p] = {}
                    s = s[p]
        if self._auto_save == 0:
            self.save()

    def save(self):
        with open(self._settings_file, 'w+') as fp:
            fp.write(json.dumps(self._settings, indent='    ', sort_keys=True))

    def __enter__(self):
        self._auto_save += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._auto_save -= 1
        if self._auto_save == 0:
            self.save()


settings = SettingsManager()
