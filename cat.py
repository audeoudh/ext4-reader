# Copyright 2020 Henry-Joseph Audéoud & Timothy Claeys
#
# This file is part of ext4-reader.
#
# ext4-reader is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ext4-reader is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with ext4-reader.  If not, see
# <https://www.gnu.org/licenses/>.

import sys

from ext4 import Filesystem, FileType


def main(block_device, path):
    try:
        with Filesystem(block_device) as filesystem:
            # Obtaining list of files to display
            file = filesystem.get_file(path)
            if file.get_file_type() == FileType.IFREG:
                print(file.content.get_bytes().decode('utf-8'), end="")
            else:
                print(f"{path}: is not a regular file", file=sys.stderr)
                sys.exit(1)
    except PermissionError:
        print(f"{block_device}: permission denied", file=sys.stderr)
        sys.exit(1)


def _args_parser():
    import argparse
    parser = argparse.ArgumentParser(prog="cat", description="print file on the standard output")
    parser.add_argument("block_device",
                        help="Path to the block device containing the ext4 file system")
    parser.add_argument("path", metavar="FILE",
                        help="Print FILE to standard output.")
    return parser


if __name__ == '__main__':
    _parser = _args_parser()
    opts = _parser.parse_args()
    main(**vars(opts))
