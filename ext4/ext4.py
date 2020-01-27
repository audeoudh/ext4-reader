import enum
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
    def __init__(self, block_device):
        self.block_device = block_device
        self.fd = ...
        self.conf: Superblock = ...

    def __enter__(self):
        self.fd = os.open(self.block_device, os.O_RDONLY)
        # 1024s hardcoded here, because we do not know anything about the filesystem currently
        superblock = self.get_bytes(0x400, 1024)
        self.conf = Superblock().read_bytes(superblock)
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

    def get_block(self, index, n=1):
        return self.get_bytes(index * self.conf.get_block_size(), n * self.conf.get_block_size())

    def get_block_group_desc(self, bg_no, strict=True) -> BlockGroupDescriptor:
        # Compute block group position
        # FIXME: What if superblock does not exist?  Or block group descriptors do not exist??
        if self.conf.has_flag(Superblock.FeatureIncompat.INCOMPAT_FLEX_BG):
            groups_per_flex = self.conf.get_groups_per_flex()
            main_bg_no = bg_no // groups_per_flex * groups_per_flex
            index_in_flex = bg_no % groups_per_flex
            if self.conf.has_flag(Superblock.FeatureIncompat.INCOMPAT_64BIT):
                index_in_flex = 64 * index_in_flex
            else:
                index_in_flex = 32 * index_in_flex
            superblock_size = self.conf.get_block_size()
            bgd_pos = main_bg_no * self.conf.s_blocks_per_group \
                   + superblock_size + index_in_flex
        else:
            superblock_size = self.conf.get_block_size()
            bgd_pos = bg_no * self.conf.s_blocks_per_group + superblock_size
        # Retrieve and parse data
        if self.conf.has_flag(Superblock.FeatureIncompat.INCOMPAT_64BIT):
            return BlockGroupDescriptor64(self, bg_no, bgd_pos) \
                .read_bytes(self.get_bytes(bgd_pos, 64), strict=strict)
        else:
            return BlockGroupDescriptor(self, bg_no, bgd_pos) \
                .read_bytes(self.get_bytes(bgd_pos, 32), strict=strict)

    def get_inode(self, inode_no, strict=True) -> Inode:
        # Compute inode position
        bg_no = (inode_no - 1) // self.conf.s_inodes_per_group
        bgd = self.get_block_group_desc(bg_no, strict=strict)
        inode_index = (inode_no - 1) % self.conf.s_inodes_per_group
        inode_pos = bgd.get_inode_table_loc() + self.conf.s_inode_size * inode_index
        # Retrieve and parse data
        struct_data = self.get_bytes(inode_pos, self.conf.s_inode_size)
        inode = Inode(self, inode_no, inode_pos).read_bytes(struct_data, strict=strict)
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
