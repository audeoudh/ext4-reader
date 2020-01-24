import enum
import os

from .files import Directory, File
from .data_structures import Superblock


# Reference: https://ext4.wiki.kernel.org/index.php/Ext4_Disk_Layout#Directory_Entries


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
