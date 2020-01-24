import enum
import os

from ext4.files import Directory, File
from .data_structures import Superblock, BlockGroupDescriptor, BlockGroupDescriptor64


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


class BlockGroup:
    def __init__(self, filesystem, group_number):
        self.filesystem = filesystem
        self.group_number = group_number
        self.desc: BlockGroupDescriptor
        if self.filesystem.conf.s_feature_incompat & Superblock.FeatureIncompat.INCOMPAT_64BIT == 0:
            self.desc = BlockGroupDescriptor(self.filesystem) \
                .read_bytes(self.group_number, self.filesystem.get_block(self._first_block_no() + 1))
        else:
            self.desc = BlockGroupDescriptor64(self.filesystem) \
                .read_bytes(self.group_number, self.filesystem.get_block(self._first_block_no() + 1))

    def _first_block_no(self):
        return self.group_number * self.filesystem.conf.s_blocks_per_group

    def has_superblock(self):
        # See https://stackoverflow.com/questions/1804311/how-to-check-if-an-integer-is-a-power-of-3
        # for power of {3, 5, 7} checks
        return (self.filesystem.conf.s_feature_ro_compat & Superblock.RO_COMPAT_SPARSE_SUPER) == 0 \
               or (self.group_number == 0) \
               or (3**20 % self.group_number == 0) \
               or (5**13 % self.group_number == 0) \
               or (7**11 % self.group_number == 0)

    def has_group_descriptors(self):
        return self.has_superblock()


class Filesystem:
    def __init__(self, block_device):
        self.block_device = block_device
        self.fd = ...
        self.conf: Superblock = ...

    def __enter__(self):
        self.fd = os.open(self.block_device, os.O_RDONLY)
        # 1024s hardcoded here, because we do not know anything about the filesystem currently
        superblock = self._get_bytes(0x400, 1024)
        self.conf = Superblock().read_bytes(superblock)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.close(self.fd)

    @property
    def UUID(self):
        return self.conf.s_uuid

    def _get_bytes(self, offset, length):
        try:
            os.lseek(self.fd, offset, os.SEEK_SET)
        except OSError as ose:
            if ose.errno == 22:
                ose.strerror += f" (fd={self.fd}, offset={offset}, whence=SEEK_SET)"
            raise ose
        b = os.read(self.fd, length)
        return b

    def get_block_group_desc(self, bg_no):
        return BlockGroup(self, bg_no).desc

    def get_block(self, index, n=1):
        return self._get_bytes(index * self.conf.block_size, n * self.conf.block_size)

    def _get_inode(self, inode_no):
        raise NotImplementedError

    def get_file(self, path) -> File:
        if not path.startswith("/"):
            raise ValueError("Path must be absolute")
        cwd = self.get_root_dir()
        path = path[1:]
        if path == "":
            return cwd
        return cwd.get_file(path)

    def get_root_dir(self) -> Directory:
        return Directory(self, "/", SpecialInode.ROOT_DIRECTORY, self._get_inode(SpecialInode.ROOT_DIRECTORY))
