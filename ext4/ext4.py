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

import enum
import functools
import os

from ext4.files import Directory, File
from .data_structures import \
    Superblock, BlockGroupDescriptor, BlockGroupDescriptor64, Inode


class SpecialInode(enum.IntEnum):
    NULL = 0
    DEFECTIVE_BLOCKS = 1
    ROOT_DIRECTORY = 2
    USER_QUOTA = 3
    GROUP_QUOTA = 4
    BOOT_LOADER = 5
    UNDELETE_DIRECTORY = 6
    RESERVED_GROUP_DESCRIPTORS = 7
    JOURNAL = 8
    EXCLUDE = 9
    REPLICA = 10
    FIRST_NON_REVERSED = 11


class Filesystem:
    fail_on_wrong_checksum = True

    def __init__(self, block_device):
        self.block_device = block_device
        self.fd = ...
        self.conf: Superblock = ...

    def __enter__(self):
        self.fd = os.open(self.block_device, os.O_RDONLY)
        # 1024s hardcoded here, because we do not know anything about the filesystem currently
        superblock = self.get_bytes(0x400, 1024)
        self.conf = Superblock(self).read_bytes(superblock)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.close(self.fd)

    @property
    def UUID(self):
        return self.conf.s_uuid

    def get_bytes(self, offset, length):
        try:
            os.lseek(self.fd, offset, os.SEEK_SET)
        except OSError as ose:
            if ose.errno == 22:
                ose.strerror += f" (fd={self.fd}, offset={offset}, whence=SEEK_SET)"
            raise ose
        b = os.read(self.fd, length)
        return b

    def has_superblock(self, bg_no):
        # See https://stackoverflow.com/questions/1804311/how-to-check-if-an-integer-is-a-power-of-3
        # for power of {3, 5, 7} checks
        return (not self.conf.has_flag(Superblock.FeatureRoCompat.RO_COMPAT_SPARSE_SUPER)) \
               or (bg_no == 0) \
               or (3 ** 20 % bg_no == 0) \
               or (5 ** 13 % bg_no == 0) \
               or (7 ** 11 % bg_no == 0)

    def get_block(self, index, n=1):
        return self.get_bytes(index * self.conf.get_block_size(), n * self.conf.get_block_size())

    @functools.lru_cache(32)  # 128B per entry
    def get_block_group_desc(self, bg_no) -> BlockGroupDescriptor:
        # Compute block group position
        bgd_size = self.conf.s_desc_size if self.conf.has_flag(self.conf.FeatureIncompat.INCOMPAT_64BIT) else 32
        bgd_per_block = self.conf.get_block_size() // bgd_size
        if self.conf.has_flag(Superblock.FeatureRoCompat.RO_COMPAT_SPARSE_SUPER):
            # All block groups descriptors are in block group 0
            superblock_size = 1
            block_no = superblock_size + (bg_no // bgd_per_block)
            offset_in_block = bg_no % bgd_per_block * bgd_size
        elif self.conf.has_flag(Superblock.FeatureIncompat.INCOMPAT_FLEX_BG):
            # Block group descriptors are in first block group of the flex
            groups_per_flex = self.conf.get_groups_per_flex()
            index_in_flex = bg_no % groups_per_flex
            main_bg_no = bg_no - index_in_flex
            superblock_size = 1 if self.has_superblock(main_bg_no) else 0
            block_no = main_bg_no * self.conf.s_blocks_per_group + superblock_size + (index_in_flex // bgd_per_block)
            offset_in_block = index_in_flex % bgd_per_block * bgd_size
        else:
            # FIXME where are block descriptors in this situation?
            raise NotImplementedError
        bgd_pos = block_no * self.conf.get_block_size() + offset_in_block
        # Retrieve and parse data
        if self.conf.has_flag(Superblock.FeatureIncompat.INCOMPAT_64BIT):
            return BlockGroupDescriptor64(self, bg_no, bgd_pos) \
                .read_bytes(self.get_bytes(bgd_pos, 64))
        else:
            return BlockGroupDescriptor(self, bg_no, bgd_pos) \
                .read_bytes(self.get_bytes(bgd_pos, 32))

    def get_inode(self, inode_no) -> Inode:
        # Compute inode position
        bg_no = (inode_no - 1) // self.conf.s_inodes_per_group
        bgd = self.get_block_group_desc(bg_no)
        inode_index = (inode_no - 1) % self.conf.s_inodes_per_group
        inode_pos = bgd.get_inode_table_loc() * self.conf.get_block_size() + self.conf.s_inode_size * inode_index
        # Retrieve and parse data
        struct_data = self.get_bytes(inode_pos, self.conf.s_inode_size)
        inode = Inode(self, inode_no, inode_pos).read_bytes(struct_data)
        return inode

    def get_file(self, path) -> File:
        if not path.startswith("/"):
            raise ValueError("Path must be absolute")
        cwd = self.get_root_dir()
        path = path[1:]
        if path == "":
            return cwd
        return cwd.get_file(path)

    def get_root_dir(self) -> Directory:
        return Directory(self, "/", SpecialInode.ROOT_DIRECTORY, self.get_inode(SpecialInode.ROOT_DIRECTORY))
