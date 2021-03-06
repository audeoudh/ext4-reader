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

import ctypes
import enum

from . import logger, tools
from .tools import FSException, crc16, crc32c


class Superblock(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("s_inodes_count", ctypes.c_uint32),
        ("s_blocks_count_lo", ctypes.c_uint32),
        ("s_r_blocks_count_lo", ctypes.c_uint32),
        ("s_free_blocks_count_lo", ctypes.c_uint32),
        ("s_free_inodes_count", ctypes.c_uint32),
        ("s_first_data_block", ctypes.c_uint32),
        ("s_log_block_size", ctypes.c_uint32),
        ("s_log_cluster_size", ctypes.c_uint32),
        ("s_blocks_per_group", ctypes.c_uint32),
        ("s_clusters_per_group", ctypes.c_uint32),
        ("s_inodes_per_group", ctypes.c_uint32),
        ("s_mtime", ctypes.c_uint32),
        ("s_wtime", ctypes.c_uint32),
        ("s_mnt_count", ctypes.c_uint16),
        ("s_max_mnt_count", ctypes.c_uint16),
        ("s_magic", ctypes.c_uint16),
        ("s_state", ctypes.c_uint16),
        ("s_errors", ctypes.c_uint16),
        ("s_minor_rev_level", ctypes.c_uint16),
        ("s_lastcheck", ctypes.c_uint32),
        ("s_checkinterval", ctypes.c_uint32),
        ("s_creator_os", ctypes.c_uint32),
        ("s_rev_level", ctypes.c_uint32),
        ("s_def_resuid", ctypes.c_uint16),
        ("s_def_resgid", ctypes.c_uint16),

        ("s_first_ino", ctypes.c_uint32),
        ("s_inode_size", ctypes.c_uint16),
        ("s_block_group_nr", ctypes.c_uint16),
        ("s_feature_compat", ctypes.c_uint32),
        ("s_feature_incompat", ctypes.c_uint32),
        ("s_feature_ro_compat", ctypes.c_uint32),
        ("s_uuid", ctypes.c_uint8 * 16),
        ("s_volume_name", ctypes.c_ubyte * 16),
        ("s_last_mounted", ctypes.c_ubyte * 64),
        ("s_algorithm_usage_bitmap", ctypes.c_uint32),

        ("s_prealloc_blocks", ctypes.c_uint8),
        ("s_prealloc_dir_blocks", ctypes.c_uint8),
        ("s_reserved_gdt_blocks", ctypes.c_uint16),

        ("s_journal_uuid", ctypes.c_uint8 * 16),
        ("s_journal_inum", ctypes.c_uint32),
        ("s_journal_dev", ctypes.c_uint32),
        ("s_last_orphan", ctypes.c_uint32),
        ("s_hash_seed", ctypes.c_uint32 * 4),
        ("s_def_hash_version", ctypes.c_uint8),
        ("s_jnl_backup_type", ctypes.c_uint8),
        ("s_desc_size", ctypes.c_uint16),
        ("s_default_mount_opts", ctypes.c_uint32),
        ("s_first_meta_bg", ctypes.c_uint32),
        ("s_mkfs_time", ctypes.c_uint32),
        ("s_jnl_blocks", ctypes.c_uint32 * 17),

        ("s_blocks_count_hi", ctypes.c_uint32),
        ("s_r_blocks_count_hi", ctypes.c_uint32),
        ("s_free_blocks_count_hi", ctypes.c_uint32),
        ("s_min_extra_isize", ctypes.c_uint16),
        ("s_want_extra_isize", ctypes.c_uint16),
        ("s_flags", ctypes.c_uint32),
        ("s_raid_stride", ctypes.c_uint16),
        ("s_mmp_interval", ctypes.c_uint16),
        ("s_mmp_block", ctypes.c_uint64),
        ("s_raid_stripe_width", ctypes.c_uint32),
        ("s_log_groups_per_flex", ctypes.c_uint8),
        ("s_checksum_type", ctypes.c_uint8),
        ("s_reserved_pad", ctypes.c_uint16),
        ("s_kbytes_written", ctypes.c_uint64),
        ("s_snapshot_inum", ctypes.c_uint32),
        ("s_snapshot_id", ctypes.c_uint32),
        ("s_snapshot_r_blocks_count", ctypes.c_uint64),
        ("s_snapshot_list", ctypes.c_uint32),
        ("s_error_count", ctypes.c_uint32),
        ("s_first_error_time", ctypes.c_uint32),
        ("s_first_error_ino", ctypes.c_uint32),
        ("s_first_error_block", ctypes.c_uint64),
        ("s_first_error_func", ctypes.c_uint8 * 32),
        ("s_first_error_line", ctypes.c_uint32),
        ("s_last_error_time", ctypes.c_uint32),
        ("s_last_error_ino", ctypes.c_uint32),
        ("s_last_error_line", ctypes.c_uint32),
        ("s_last_error_block", ctypes.c_uint64),
        ("s_last_error_func", ctypes.c_uint8 * 32),
        ("s_mount_opts", ctypes.c_uint8 * 64),
        ("s_usr_quota_inum", ctypes.c_uint32),
        ("s_grp_quota_inum", ctypes.c_uint32),
        ("s_overhead_blocks", ctypes.c_uint32),
        ("s_backup_bgs", ctypes.c_uint32 * 2),
        ("s_encrypt_algos", ctypes.c_uint8 * 4),
        ("s_encrypt_pw_salt", ctypes.c_uint8 * 16),
        ("s_lpf_ino", ctypes.c_uint32),
        ("s_prj_quota_inum", ctypes.c_uint32),
        ("s_checksum_seed", ctypes.c_uint32),
        ("s_reserved", ctypes.c_uint32 * 98),
        ("s_checksum", ctypes.c_uint32),
    ]

    def __init__(self, filesystem):
        super().__init__()
        self.filesystem = filesystem

    def read_bytes(self, struct_data):
        fit = min(len(struct_data), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), struct_data, fit)
        if self.filesystem.fail_on_wrong_checksum \
                and not self.verify_checksums(struct_data):
            raise FSException(f"Wrong checksum in superblock")
        logger.info("Decoded superbock: FS UUID = %s", self._format_uuid())
        return self

    def _format_uuid(self):
        return "%02x%02x%02x%02x-%02x%02x-%02x%02x-%02x%02x-%02x%02x%02x%02x%02x%02x" % tuple(self.s_uuid)

    def verify_checksums(self, struct_data):
        if self.s_feature_ro_compat & Superblock.FeatureRoCompat.RO_COMPAT_METADATA_CSUM != 0:
            data = struct_data[:0x3FC]
            csum = crc32c(data)
            return csum == self.s_checksum
        return True  # Nothing to check

    # Some accelerators

    def get_block_size(self):
        return 2 ** (10 + self.s_log_block_size)

    def get_groups_per_flex(self):
        return 2 ** self.s_log_groups_per_flex

    def get_volume_name(self):
        return bytes(self.s_volume_name).decode('utf-8')

    def has_flag(self, flag):
        if isinstance(flag, self.FeatureIncompat):
            return self.s_feature_incompat & flag != 0
        elif isinstance(flag, self.FeatureRoCompat):
            return self.s_feature_ro_compat & flag != 0
        else:
            raise FSException(f"Unknown flag {flag}")

    def get_csum_seed(self):
        if self.filesystem.conf.has_flag(Superblock.FeatureIncompat.INCOMPAT_CSUM_SEED):
            return self.filesystem.conf.s_checksum_seed
        else:
            return crc32c(self.filesystem.UUID)


    # Field types

    class CreatorOS(enum.IntEnum):
        LINUX = 0
        HURD = 1
        MASIX = 2
        FEREBSD = 3
        LITES = 4

    class FeatureCompat(enum.IntEnum):
        COMPAT_DIR_PREALLOC = 0x1
        COMPAT_IMAGIC_INODES = 0x2
        COMPAT_HAS_JOURNAL = 0x4
        COMPAT_EXT_ATTR = 0x8
        COMPAT_RESIZE_INODE = 0x10
        COMPAT_DIR_INDEX = 0x20
        COMPAT_LAZY_BG = 0x40
        COMPAT_EXCLUDE_INODE = 0x80
        COMPAT_EXCLUDE_BITMAP = 0x100
        COMPAT_SPARSE_SUPER2 = 0x200

    class FeatureIncompat(enum.IntEnum):
        INCOMPAT_COMPRESSION = 0x1
        INCOMPAT_FILETYPE = 0x2
        INCOMPAT_RECOVER = 0x4
        INCOMPAT_JOURNAL_DEV = 0x8
        INCOMPAT_META_BG = 0x10
        INCOMPAT_EXTENTS = 0x40
        INCOMPAT_64BIT = 0x80
        INCOMPAT_MMP = 0x100
        INCOMPAT_FLEX_BG = 0x200
        INCOMPAT_EA_INODE = 0x400
        INCOMPAT_DIRDATA = 0x1000
        INCOMPAT_CSUM_SEED = 0x2000
        INCOMPAT_LARGEDIR = 0x4000
        INCOMPAT_INLINE_DATA = 0x8000
        INCOMPAT_ENCRYPT = 0x10000

    class FeatureRoCompat(enum.IntEnum):
        RO_COMPAT_SPARSE_SUPER = 0x1
        RO_COMPAT_LARGE_FILE = 0x2
        RO_COMPAT_BTREE_DIR = 0x4
        RO_COMPAT_HUGE_FILE = 0x8
        RO_COMPAT_GDT_CSUM = 0x10
        RO_COMPAT_DIR_NLINK = 0x20
        RO_COMPAT_EXTRA_ISIZE = 0x40
        RO_COMPAT_HAS_SNAPSHOT = 0x80
        RO_COMPAT_QUOTA = 0x100
        RO_COMPAT_BIGALLOC = 0x200
        RO_COMPAT_METADATA_CSUM = 0x400
        RO_COMPAT_REPLICA = 0x800
        RO_COMPAT_READONLY = 0x1000
        RO_COMPAT_PROJECT = 0x2000


class BlockGroupDescriptor(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("bg_block_bitmap_lo", ctypes.c_uint32),
        ("bg_inode_bitmap_lo", ctypes.c_uint32),
        ("bg_inode_table_lo", ctypes.c_uint32),
        ("bg_free_blocks_count_lo", ctypes.c_uint16),
        ("bg_free_inodes_count_lo", ctypes.c_uint16),
        ("bg_used_dirs_count_lo", ctypes.c_uint16),
        ("bg_flags", ctypes.c_uint16),
        ("bg_exclude_bitmap_lo", ctypes.c_uint32),
        ("bg_block_bitmap_csum_lo", ctypes.c_uint16),
        ("bg_inode_bitmap_csum_lo", ctypes.c_uint16),
        ("bg_itable_unused_lo", ctypes.c_uint16),
        ("bg_checksum", ctypes.c_uint16)
    ]

    def __init__(self, filesystem, bg_no, bgd_pos):
        super().__init__()
        self.filesystem = filesystem
        self.no = bg_no
        self.pos = bgd_pos

    def read_bytes(self, struct_data):
        fit = min(len(struct_data), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), struct_data, fit)
        if self.filesystem.fail_on_wrong_checksum \
                and not self.verify_checksums():
            raise FSException(f"Wrong checksum in block group descriptor {self.no}")
        logger.info("Decoded block group descriptor %d (@%X)", self.no, self.pos)
        return self

    def verify_checksums(self):
        data = bytes(self.filesystem.UUID) + self.no.to_bytes(4, 'little') + bytes(self)[:0x1E]
        csum = self._get_checksum_algo()(data) & 0xFFFF
        return csum == self.bg_checksum

    def _get_checksum_algo(self):
        if self.filesystem.conf.s_feature_ro_compat & Superblock.FeatureRoCompat.RO_COMPAT_GDT_CSUM != 0 \
                and self.filesystem.conf.s_feature_ro_compat & Superblock.FeatureRoCompat.RO_COMPAT_METADATA_CSUM == 0:
            return crc16
        elif self.filesystem.conf.s_feature_ro_compat & Superblock.FeatureRoCompat.RO_COMPAT_METADATA_CSUM != 0:
            return crc32c
        else:
            raise FSException("Unknown checksum method")


    # Some accelerators

    def get_bg_block_bitmap_loc(self):
        return self.bg_block_bitmap_lo

    def get_bg_inode_bitmap_loc(self):
        return self.bg_inode_bitmap_lo

    def get_inode_table_loc(self):
        return self.bg_inode_table_lo

    def has_flag(self, flag):
        return self.bg_flags & flag != 0

    # Field types

    class Flags(enum.IntEnum):
        INODE_UNINIT = 0x1
        BLOCK_UNINIT = 0x2
        INODE_ZEROED = 0x4


class BlockGroupDescriptor64(BlockGroupDescriptor):
    _fields_ = [
        ("bg_block_bitmap_hi", ctypes.c_uint32),
        ("bg_inode_bitmap_hi", ctypes.c_uint32),
        ("bg_inode_table_hi", ctypes.c_uint32),
        ("bg_free_blocks_count_hi", ctypes.c_uint16),
        ("bg_free_inodes_count_hi", ctypes.c_uint16),
        ("bg_used_dirs_count_hi", ctypes.c_uint16),
        ("bg_itable_unused_hi", ctypes.c_uint16),
        ("bg_exclude_bitmap_hi", ctypes.c_uint32),
        ("bg_block_bitmap_csum_hi", ctypes.c_uint16),
        ("bg_inode_bitmap_csum_hi", ctypes.c_uint16),
        ("bg_reserved", ctypes.c_uint32)
    ]

    def verify_checksums(self):
        data = bytes(self.filesystem.UUID) + self.no.to_bytes(4, 'little') + bytes(self)[:0x1E] \
               + b"\x00\x00" + bytes(self)[0x20:]
        csum = self._get_checksum_algo()(data) & 0xFFFF
        return csum == self.bg_checksum

    def get_bg_block_bitmap_loc(self):
        return (self.bg_block_bitmap_hi << 32) + self.bg_block_bitmap_lo

    def get_bg_inode_bitmap_loc(self):
        return (self.bg_inode_bitmap_hi << 32) + self.bg_inode_bitmap_lo

    def get_inode_table_loc(self):
        return (self.bg_inode_table_hi << 32) + self.bg_inode_table_lo


# Inodes

class _Inode_Linux1(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('l_i_version', ctypes.c_uint32)
    ]


class _Inode_Hurd1(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('h_i_translator', ctypes.c_uint32)
    ]


class _Inode_Masix1(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_i_reserved', ctypes.c_uint32)
    ]


class _Inode_Osd1(ctypes.Union):
    _pack_ = 1
    _fields_ = [
        ('linux1', _Inode_Linux1),
        ('hurd1', _Inode_Hurd1),
        ('masix1', _Inode_Masix1)
    ]


class _Inode_Linux2(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('l_i_blocks_high', ctypes.c_uint16),
        ('l_i_file_acl_high', ctypes.c_uint16),
        ('l_i_uid_high', ctypes.c_uint16),
        ('l_i_gid_high', ctypes.c_uint16),
        ('l_i_checksum_lo', ctypes.c_uint16),
        ('l_i_reserved', ctypes.c_uint16)
    ]


class _Inode_Hurd2(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('h_i_reserved1', ctypes.c_uint16),
        ('h_i_mode_high', ctypes.c_uint16),
        ('h_i_uid_high', ctypes.c_uint16),
        ('h_i_gid_high', ctypes.c_uint16),
        ('h_i_author', ctypes.c_uint32)
    ]


class _Inode_Masix2(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('m_i_reserved1', ctypes.c_uint16),
        ('m_i_file_acl_high', ctypes.c_uint16),
        ('m_i_reserved2', ctypes.c_uint32)
    ]


class _Inode_Osd2(ctypes.Union):
    _pack_ = 1
    _fields_ = [
        ('linux2', _Inode_Linux2),
        ('hurd2', _Inode_Hurd2),
        ('masix2', _Inode_Masix2)
    ]


class Inode(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("i_mode", ctypes.c_uint16),
        ("i_uid", ctypes.c_uint16),
        ("i_size_lo", ctypes.c_uint32),
        ("i_atime", ctypes.c_uint32),
        ("i_ctime", ctypes.c_uint32),
        ("i_mtime", ctypes.c_uint32),
        ("i_dtime", ctypes.c_uint32),
        ("i_gid", ctypes.c_uint16),
        ("i_links_count", ctypes.c_uint16),
        ("i_blocks_lo", ctypes.c_uint32),
        ("i_flags", ctypes.c_uint32),
        ("i_osd1", _Inode_Osd1),
        ("i_block", ctypes.c_uint32 * 15),
        ("i_generation", ctypes.c_uint32),
        ("i_file_acl_lo", ctypes.c_uint32),
        ("i_size_high", ctypes.c_uint32),
        ("i_obso_faddr", ctypes.c_uint32),
        ("i_osd2", _Inode_Osd2),
        ("i_extra_isize", ctypes.c_uint16),
        ("i_checksum_hi", ctypes.c_uint16),
        ("i_ctime_extra", ctypes.c_uint32),
        ("i_mtime_extra", ctypes.c_uint32),
        ("i_atime_extra", ctypes.c_uint32),
        ("i_crtime", ctypes.c_uint32),
        ("i_crtime_extra", ctypes.c_uint32),
        ("i_version_hi", ctypes.c_uint32),
        ("i_projid", ctypes.c_uint32)
    ]

    EXT2_GOOD_OLD_INODE_SIZE = 128

    def __init__(self, filesystem, inode_no, position):
        super().__init__()
        self.filesystem = filesystem
        self.no = inode_no
        self.pos = position
        self._extraneous_data = ...

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.no}>"

    def read_bytes(self, struct_data):
        if len(struct_data) < self.filesystem.conf.s_inode_size:
            raise ValueError(f"Too few data to read a inode, "
                             f"expected at least {self.filesystem.conf.s_inode_size} bytes")
        min_size = self.EXT2_GOOD_OLD_INODE_SIZE + Inode.i_extra_isize.size
        ctypes.memmove(ctypes.addressof(self), struct_data, min_size)
        ctypes.memmove(ctypes.addressof(self) + min_size, struct_data[min_size:],
                       self.i_extra_isize - Inode.i_extra_isize.size)
        self._extraneous_data = struct_data[self.EXT2_GOOD_OLD_INODE_SIZE + self.i_extra_isize:
                                            self.filesystem.conf.s_inode_size]
        if self.filesystem.fail_on_wrong_checksum \
                and not self.verify_checksums():
            raise FSException(f"Wrong checksum in inode {self.no}")
        return self

    def verify_checksums(self):
        if not self.filesystem.conf.has_flag(Superblock.FeatureRoCompat.RO_COMPAT_METADATA_CSUM):
            return True  # No checksums
        has_hi = self.i_extra_isize > Inode.i_extra_isize.size
        has_lo = self.filesystem.conf.s_creator_os == Superblock.CreatorOS.LINUX
        if not has_hi and not has_lo:
            return True  # Nothing to check
        # Compute expected checksum
        seed = self.filesystem.conf.get_csum_seed()
        checksum_lo_start = Inode.i_osd2.offset + _Inode_Linux2.l_i_checksum_lo.offset
        checksum_hi_start = Inode.i_checksum_hi.offset
        struct_data = bytes(self)
        crc = crc32c(self.no.to_bytes(4, 'little'), seed)
        crc = crc32c(self.i_generation.to_bytes(4, 'little'), crc)
        crc = crc32c(struct_data[:checksum_lo_start], crc)
        crc = crc32c(b"\x00" * 2 if has_lo else struct_data[checksum_lo_start:checksum_lo_start + 2], crc)
        crc = crc32c(struct_data[checksum_lo_start + 2:checksum_hi_start], crc)
        crc = crc32c(b"\x00" * 2 if has_hi else struct_data[checksum_hi_start:checksum_hi_start + 2], crc)
        crc = crc32c(struct_data[checksum_hi_start + 2:], crc)
        computed_csum = crc32c(self._extraneous_data, crc)
        if not has_hi:
            computed_csum &= 0x0000FFFF
        if not has_lo:
            computed_csum &= 0xFFFF0000
        # Get provided checksum
        provided_csum = 0
        if has_hi:
            provided_csum |= self.i_checksum_hi << 16
        if has_lo:
            provided_csum |= self.i_osd2.linux2.l_i_checksum_lo
        # Compare
        return computed_csum == provided_csum

    # Some accelerators

    def has_flag(self, flag):
        return self.i_flags & flag != 0

    def get_file_type(self):
        file_type = self.i_mode & 0xF000
        try:
            return self.Mode(file_type)
        except ValueError:
            raise FSException(f"Unknwon file type 0x{file_type:X}")

    def get_mode(self):
        return self.i_mode & 0x0FFF

    def get_size(self):
        return self.i_size_high << 32 | self.i_size_lo

    def get_ctime_ns(self):
        """Combine i_ctime and i_ctime_extra fields"""
        has_ctime_extra = self.i_extra_isize \
                          > Inode.i_ctime_extra.offset - Inode.EXT2_GOOD_OLD_INODE_SIZE
        return tools.read_timestamp_ns(self.i_ctime, self.i_ctime_extra if has_ctime_extra else None)

    def get_mtime_ns(self):
        """Combine i_mtime and i_mtime_extra fields"""
        has_mtime_extra = self.i_extra_isize \
                          > Inode.i_mtime_extra.offset - Inode.EXT2_GOOD_OLD_INODE_SIZE
        return tools.read_timestamp_ns(self.i_mtime, self.i_mtime_extra if has_mtime_extra else None)

    def get_atime_ns(self):
        """Combine i_atime and i_atime_extra fields"""
        has_atime_extra = self.i_extra_isize \
                          > Inode.i_atime_extra.offset - Inode.EXT2_GOOD_OLD_INODE_SIZE
        return tools.read_timestamp_ns(self.i_atime, self.i_atime_extra if has_atime_extra else None)

    def get_block_count(self):
        bc = self.i_blocks_lo
        # FIXME: not sure of the interpretation of the documentation
        if self.filesystem.conf.s_creator_os == Superblock.CreatorOS.LINUX:
            if self.filesystem.conf.has_flag(Superblock.FeatureRoCompat.RO_COMPAT_HUGE_FILE):
                bc += self.i_osd2.linux2.l_i_blocks_high << 32
        return bc

    def get_blocksize(self):
        if not self.filesystem.conf.has_flag(Superblock.FeatureRoCompat.RO_COMPAT_HUGE_FILE):
            return 512
        elif not self.has_flag(Inode.Flags.HUGE_FILE):
            return 512  # FIXME: that's how I understand documentation, but
                        # kernel implementation seems to prefer filesystem
                        # blocks there
        else:
            return self.filesystem.conf.get_block_size()

    # Field types

    class Mode(enum.IntEnum):
        # File mode
        IXOTH = 0x1  # Others may execute
        IWOTH = 0x2  # Others may write
        IROTH = 0x4  # Others may read
        IXGRP = 0x8  # Group members may execute
        IWGRP = 0x10  # Group members may write
        IRGRP = 0x20  # Group members may read
        IXUSR = 0x40  # Owner may execute
        IWUSR = 0x80  # Owner may write
        IRUSR = 0x100  # Owner may read
        ISVTX = 0x200  # Sticky bit
        ISGID = 0x400  # Set GID
        ISUID = 0x800  # Set UID

        # These are mutually-exclusive file types:
        IFIFO = 0x1000  # FIFO
        IFCHR = 0x2000  # Character device
        IFDIR = 0x4000  # Directory
        IFBLK = 0x6000  # Block device
        IFREG = 0x8000  # Regular file
        IFLNK = 0xA000  # Symbolic link
        IFSOCK = 0xC000  # Socket

    class Flags(enum.IntEnum):
        SECRM = 0x1
        UNRM = 0x2
        COMPR = 0x4
        SYNC = 0x8
        IMMUTABLE = 0x10
        APPEND = 0x20
        NODUMP = 0x40
        NOATIME = 0x80
        DIRTY = 0x100
        COMPRBLK = 0x200
        NOCOMPR = 0x400
        ENCRYPT = 0x800
        INDEX = 0x1000
        IMAGIC = 0x2000
        JOURNAL_DATA = 0x4000
        NOTAIL = 0x8000
        DIRSYNC = 0x10000
        TOPDIR = 0x20000
        HUGE_FILE = 0x40000
        EXTENTS = 0x80000
        EA_INODE = 0x200000
        EOFBLOCKS = 0x400000
        SNAPFILE = 0x01000000
        SNAPFILE_DELETED = 0x04000000
        SNAPFILE_SHRUNK = 0x08000000
        INLINE_DATA = 0x10000000
        PROJINHERIT = 0x20000000
        RESERVED = 0x80000000


# Inode's content

class ExtentHeader(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("eh_magic", ctypes.c_uint16),
        ("eh_entries", ctypes.c_uint16),
        ("eh_max", ctypes.c_uint16),
        ("eh_depth", ctypes.c_uint16),
        ("eh_generation", ctypes.c_uint32)
    ]

    def __init__(self, filesystem):
        super().__init__()
        self.filesystem = filesystem

    def read_bytes(self, struct_data):
        fit = min(len(struct_data), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), struct_data, fit)
        if self.filesystem.fail_on_wrong_checksum \
                and not self.magic_is_valid():
            raise FSException("Magic is not valid in extent tree header")
        return self

    # Accelerators

    def magic_is_valid(self):
        return self.eh_magic == 0xF30A


class ExtentIdx(ctypes.LittleEndianStructure):
    """Internal nodes of the extent tree."""
    _pack_ = 1
    _fields_ = [
        ("ei_block", ctypes.c_uint32),
        ("ei_leaf_lo", ctypes.c_uint32),
        ("ee_leaf_hi", ctypes.c_uint16),
        ("ee_unused", ctypes.c_uint16),
    ]

    def read_bytes(self, struct_data):
        fit = min(len(struct_data), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), struct_data, fit)
        return self


class Extent(ctypes.LittleEndianStructure):
    """Leaf nodes of the extent tree."""
    _pack_ = 1
    _fields_ = [
        ("ee_block", ctypes.c_uint32),
        ("ee_len", ctypes.c_uint16),
        ("ee_start_hi", ctypes.c_uint16),
        ("ee_start_lo", ctypes.c_uint32),
    ]

    def read_bytes(self, struct_data):
        fit = min(len(struct_data), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), struct_data, fit)
        return self

    def get_start(self):
        return (self.ee_start_hi << 32) | self.ee_start_lo


class DirEntry(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("inode", ctypes.c_uint32),
        ("rec_len", ctypes.c_uint16),
        ("name_len", ctypes.c_uint16),
        # ("name",)  # Variable length, see below
    ]

    def __init__(self):
        super().__init__()
        self._name = ...

    def read_bytes(self, struct_data):
        fit = min(len(struct_data), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), struct_data, fit)
        # Variable-length field, stored separately
        self._name = struct_data[0x08:0x08 + self.name_len]
        return self

    # Accelerators

    @property
    def name(self):
        return self._name

    def get_name(self):
        return self.name.decode('utf-8')


class DirEntry2(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("inode", ctypes.c_uint32),
        ("rec_len", ctypes.c_uint16),
        ("name_len", ctypes.c_uint8),
        ("file_type", ctypes.c_uint8),
        # ("name",)  # Variable length
    ]

    def __init__(self):
        super().__init__()
        self._name = ...

    def read_bytes(self, struct_data):
        fit = min(len(struct_data), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), struct_data, fit)
        # Variable-length field, stored separately
        self._name = struct_data[0x08:0x08 + self.name_len]
        return self

    # Accelerators

    @property
    def name(self):
        return self._name

    def get_name(self):
        return self.name.decode('utf-8')

    # Field types

    class FileType(enum.IntEnum):
        UNKNOWN = 0x0
        REGULAR_FILE = 0x1
        DIRECTORY = 0x2
        CHARACTER_DEVICE_FILE = 0x3
        BLOCK_DEVICE_FILE = 0x4
        FIFO = 0x5
        SOCKET = 0x6
        SYMBOLIC_LINK = 0x7
        DIR_ENTRY_TAIL = 0xDE

    # Accelerators

    @property
    def get_file_type(self):
        return self.FileType(self.file_type)


class DirEntryTail(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("reserved_zero1", ctypes.c_uint32),
        ("rec_len", ctypes.c_uint16),
        ("reserved_zero2", ctypes.c_uint8),
        ("reserved_ft", ctypes.c_uint8),
        ("checksum", ctypes.c_uint32)
    ]

    def read_bytes(self, struct_data):
        fit = min(len(struct_data), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), struct_data, fit)
        return self


class DxRootInfo(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("reserved_zero", ctypes.c_uint32),
        ("hash_version", ctypes.c_uint8),
        ("info_length", ctypes.c_uint8),
        ("indirect_levels", ctypes.c_uint8),
        ("unused_flags", ctypes.c_uint8)
    ]

    def read_bytes(self, struct_data):
        fit = min(len(struct_data), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), struct_data, fit)
        return self

    # Accelerators

    def get_hash_algo(self):
        return self.HashAlgo(self.hash_version).algo

    # Field types

    class HashAlgo(enum.IntEnum):
        LEGACY = 0x0
        HALF_MD4 = 0x1
        TEA = 0x2
        LEGACY_UNSIGNED = 0x3
        HALF_MD4_UNSIGNED = 0x4
        TEA_UNSIGNED = 0x5

        @property
        def algo(self):
            """Real algorithm.  None if not currently supported."""
            return [None, None, None, None, None, None][self]


class DxEntry(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("hash", ctypes.c_uint32),
        ("block", ctypes.c_uint32)
    ]

    def read_bytes(self, struct_data):
        fit = min(len(struct_data), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), struct_data, fit)
        return self


class DxTail(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("dt_reserved", ctypes.c_uint32),
        ("dt_checksum", ctypes.c_uint32)
    ]

    def read_bytes(self, struct_data):
        fit = min(len(struct_data), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), struct_data, fit)
        return self


class DxRoot(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("dot", DirEntry2),
        ("_dotname", ctypes.c_uint8 * 4),
        ("dotdot", DirEntry2),
        ("_dotdotname", ctypes.c_uint8 * 4),
        ("dx_root_info", DxRootInfo),
        ("limit", ctypes.c_uint16),
        ("count", ctypes.c_uint16),
        ("block", ctypes.c_uint32),
    ]

    def read_bytes(self, struct_data):
        fit = min(len(struct_data), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), struct_data, fit)
        self._entries_buffer = struct_data[fit:fit + (self.count - 1)]
        return self

    @property
    def entries(self):
        return self

    def __getitem__(self, index):
        return self.get_entry(index)

    def __iter__(self):
        for i in range(self.count - 1):
            yield DxEntry().read_bytes(self._entries_buffer[i * 8:])

    def get_entry(self, index):
        if not 0 <= index < self.count - 1:
            raise IndexError
        return DxEntry().read_bytes(self._entries_buffer[index * 8:])


class DxNode(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("inode", ctypes.c_uint32),
        ("rec_len", ctypes.c_uint16),
        ("name_len", ctypes.c_uint8),
        ("file_type", ctypes.c_uint8),
        ("limit", ctypes.c_uint16),
        ("count", ctypes.c_uint16),
        ("block", ctypes.c_uint32),
        ("entries", DxEntry)
    ]

    def read_bytes(self, struct_data):
        fit = min(len(struct_data), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), struct_data, fit)
        return self
