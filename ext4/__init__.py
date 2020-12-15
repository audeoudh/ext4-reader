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

import logging

logger = logging.getLogger(__name__)

from .ext4 import Filesystem
from .data_structures import Inode
FileType = Inode.Mode

__all__ = ['Filesystem', 'FileType']
