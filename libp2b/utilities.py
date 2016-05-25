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
import sys


def read_text_from_file(file_path):
    for encoding in ('utf-8', sys.getdefaultencoding(), 'utf-16le', 'utf-16be', 'windows-1250', 'windows-1251',
                     'windows-1252', 'windows-1254', 'shift-jis', 'gb2312', 'gbk', 'euc-jp', 'euc-kr', 'big5',
                     'utf-32'):
        with open(file_path, 'r', encoding=encoding) as fp:
            try:
                data = fp.read()
                return data
            except UnicodeDecodeError:
                continue


def get_image_type(file_path):
    try:
        with open(file_path, 'rb') as fp:
            header = fp.read(6)
            if header == b'GIF87a' or header == b'GIF89a':
                return 'gif'
            elif header[:4] == b'\x89\x50\x4E\x47':
                return 'png'
            elif header[:2] == b'\xFF\xD8':
                return 'jpg'
            elif header[:2] == b'BM':
                return 'bmp'
    except FileNotFoundError:
        return None


def format_size(byte_size):
    suffix = ['B', 'KB', 'MB', 'GB', 'PB']
    index = 0
    while byte_size > 1024:
        byte_size /= 1024
        index += 1
    if index >= len(suffix):
        raise RuntimeError('You seriously did not expect this to work, did you?')
    return '{:.2f} {:s}'.format(byte_size, suffix[index])


def dedent_text_and_truncate(text, max_lines):
    prefix_len = 2 ** 32
    # find shortest common space prefix
    lines = text.split('\n')
    lines = list(filter(lambda l: len(l.strip()), lines))
    for ln in lines:
        l = 0
        for c in ln:
            if c == ' ':
                l += 1
            else:
                break
        prefix_len = min(l, prefix_len)
    suffix = '...' if len(lines) > max_lines else ''
    return '\n'.join([l[prefix_len:] for l in lines[:max_lines] if l]) + suffix


def file_has_extension(filename, extensions):
    parts = filename.lower().split('.')
    if len(parts) > 1:
        return parts[-1] in extensions
    return False
