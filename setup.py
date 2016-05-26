# coding=utf-8
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
import os
import sys
import requests
import subprocess
from cx_Freeze import setup, Executable

from libp2b import const

if sys.platform == 'win32':
    base = 'Win32GUI'
else:
    base = None

if sys.argv[1] == 'build':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ui_dir = os.path.join(current_dir, 'gui', 'ui')
    for file_name in os.listdir(ui_dir):
        file_in = os.path.join(ui_dir, file_name)
        if file_name.endswith('.ui'):
            file_out = file_in[:-3] + '_ui.py'
            if not os.path.exists(file_out):
                subprocess.call(['pyside-uic', '--from-imports', '-o', file_out, file_in])
        elif file_name.endswith('.qrc'):
            file_out = file_in[:-4] + '_rc.py'
            if not os.path.exists(file_out):
                subprocess.call(['pyside-rcc', '-py3', '-o', file_out, file_in])

target_dir = os.path.join('build',
                          'exe.{sys.platform}-{sys.version_info.major}.{sys.version_info.minor}'.format(sys=sys))
gui_executable = 'p2b-gui'
certs = requests.certs.where()
setup(name='p2b-gui',
      version='1.0',
      description='Internet clipboard',
      options={
          'build_exe': {
              'icon': 'gui/ui/res/box.ico',
              'compressed': True,
              'include_files': [
                  (certs, os.path.basename(certs)),
                  ('googledrive.json', 'googledrive.json')
              ],
              'include_msvcr': True,
          },
      },
      executables=[
          Executable(gui_executable, base=base)
      ],
      )
print(os.path.join(target_dir, gui_executable + '.exe'))
subprocess.call([sys.executable, '-m', 'win32.lib.win32verstamp',
                 '--version', const.APP_VERSION_STR + '.0',
                 '--product', const.APP_NAME,
                 '--copyright', 'Copyright © Rokas Kupstys'.format(const.APP_NAME),
                 '--description', 'Internet-enabled clipboard client.',
                 os.path.join(target_dir, gui_executable + '.exe')
                 ])
