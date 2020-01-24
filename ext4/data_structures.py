import ctypes
import enum

from .tools import FSException, crc16, crc32c


class Superblock(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("s_inodes_count", ctypes.c_ulong),
        ("s_blocks_count_lo", ctypes.c_ulong),
        ("s_r_blocks_count_lo", ctypes.c_ulong),
        ("s_free_blocks_count_lo", ctypes.c_ulong),
        ("s_free_inodes_count", ctypes.c_ulong),
        ("s_first_data_block", ctypes.c_ulong),
        ("s_log_block_size", ctypes.c_ulong),
        ("s_log_cluster_size", ctypes.c_ulong),
        ("s_blocks_per_group", ctypes.c_ulong),
        ("s_clusters_per_group", ctypes.c_ulong),
        ("s_inodes_per_group", ctypes.c_ulong),
        ("s_mtime", ctypes.c_ulong),
        ("s_wtime", ctypes.c_ulong),
        ("s_mnt_count", ctypes.c_ushort),
        ("s_max_mnt_count", ctypes.c_ushort),
        ("s_magic", ctypes.c_ushort),
        ("s_state", ctypes.c_ushort),
        ("s_errors", ctypes.c_ushort),
        ("s_minor_rev_level", ctypes.c_ushort),
        ("s_lastcheck", ctypes.c_ulong),
        ("s_checkinterval", ctypes.c_ulong),
        ("s_creator_os", ctypes.c_ulong),
        ("s_rev_level", ctypes.c_ulong),
        ("s_def_resuid", ctypes.c_ushort),
        ("s_def_resgid", ctypes.c_ushort),

        ("s_first_ino", ctypes.c_ulong),
        ("s_inode_size", ctypes.c_ushort),
        ("s_block_group_nr", ctypes.c_ushort),
        ("s_feature_compat", ctypes.c_ulong),
        ("s_feature_incompat", ctypes.c_ulong),
        ("s_feature_ro_compat", ctypes.c_ulong),
        ("s_uuid", ctypes.c_ubyte * 16),
        ("s_volume_name", ctypes.c_char * 16),
        ("s_last_mounted", ctypes.c_char * 64),
        ("s_algorithm_usage_bitmap", ctypes.c_ulong),

        ("s_prealloc_blocks", ctypes.c_ubyte),
        ("s_prealloc_dir_blocks", ctypes.c_ubyte),
        ("s_reserved_gdt_blocks", ctypes.c_ushort),

        ("s_journal_uuid", ctypes.c_ubyte * 16),
        ("s_journal_inum", ctypes.c_ulong),
        ("s_journal_dev", ctypes.c_ulong),
        ("s_last_orphan", ctypes.c_ulong),
        ("s_hash_seed", ctypes.c_ulong * 4),
        ("s_def_hash_version", ctypes.c_ubyte),
        ("s_jnl_backup_type", ctypes.c_ubyte),
        ("s_desc_size", ctypes.c_ushort),
        ("s_default_mount_opts", ctypes.c_ulong),
        ("s_first_meta_bg", ctypes.c_ulong),
        ("s_mkfs_time", ctypes.c_ulong),
        ("s_jnl_blocks", ctypes.c_ulong * 17),

        ("s_blocks_count_hi", ctypes.c_ulong),
        ("s_r_blocks_count_hi", ctypes.c_ulong),
        ("s_free_blocks_count_hi", ctypes.c_ulong),
        ("s_min_extra_isize", ctypes.c_ushort),
        ("s_want_extra_isize", ctypes.c_ushort),
        ("s_flags", ctypes.c_ulong),
        ("s_raid_stride", ctypes.c_ushort),
        ("s_mmp_interval", ctypes.c_ushort),
        ("s_mmp_block", ctypes.c_ulonglong),
        ("s_raid_stripe_width", ctypes.c_ulong),
        ("s_log_groups_per_flex", ctypes.c_ubyte),
        ("s_checksum_type", ctypes.c_ubyte),
        ("s_reserved_pad", ctypes.c_ushort),
        ("s_kbytes_written", ctypes.c_ulonglong),
        ("s_snapshot_inum", ctypes.c_ulong),
        ("s_snapshot_id", ctypes.c_ulong),
        ("s_snapshot_r_blocks_count", ctypes.c_ulonglong),
        ("s_snapshot_list", ctypes.c_ulong),
        ("s_error_count", ctypes.c_ulong),
        ("s_first_error_time", ctypes.c_ulong),
        ("s_first_error_ino", ctypes.c_ulong),
        ("s_first_error_block", ctypes.c_ulonglong),
        ("s_first_error_func", ctypes.c_ubyte * 32),
        ("s_first_error_line", ctypes.c_ulong),
        ("s_last_error_time", ctypes.c_ulong),
        ("s_last_error_ino", ctypes.c_ulong),
        ("s_last_error_line", ctypes.c_ulong),
        ("s_last_error_block", ctypes.c_ulonglong),
        ("s_last_error_func", ctypes.c_ubyte * 32),
        ("s_mount_opts", ctypes.c_ubyte * 64),
        ("s_usr_quota_inum", ctypes.c_ulong),
        ("s_grp_quota_inum", ctypes.c_ulong),
        ("s_overhead_blocks", ctypes.c_ulong),
        ("s_backup_bgs", ctypes.c_ulong * 2),
        ("s_encrypt_algos", ctypes.c_ubyte * 4),
        ("s_encrypt_pw_salt", ctypes.c_ubyte * 16),
        ("s_lpf_ino", ctypes.c_ulong),
        ("s_prj_quota_inum", ctypes.c_ulong),
        ("s_checksum_seed", ctypes.c_ulong),
        ("s_reserved", ctypes.c_ulong * 98),
        ("s_checksum", ctypes.c_ulong),
    ]

    def read_bytes(self, struct_data):
        fit = min(len(struct_data), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), struct_data, fit)
        self._verify_checksums(struct_data)
        return self

    def _verify_checksums(self, struct_data):
        if self.s_feature_ro_compat & Superblock.FeatureRoCompat.RO_COMPAT_METADATA_CSUM != 0:
            data = struct_data[:0x3FC]
            csum = crc32c(data)
            if csum != self.s_checksum:
                raise FSException(f"Wrong checksum in superblock")

    # Some accelerators

    @property
    def block_size(self):
        return 2 ** (10 + self.s_log_block_size)

    # Field types

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


class BlockGroupDescriptor(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("bg_block_bitmap_lo", ctypes.c_ulong),
        ("bg_inode_bitmap_lo", ctypes.c_ulong),
        ("bg_inode_table_lo", ctypes.c_ulong),
        ("bg_free_blocks_count_lo", ctypes.c_ushort),
        ("bg_free_inodes_count_lo", ctypes.c_ushort),
        ("bg_used_dirs_count_lo", ctypes.c_ushort),
        ("bg_flags", ctypes.c_ushort),
        ("bg_exclude_bitmap_lo", ctypes.c_ulong),
        ("bg_block_bitmap_csum_lo", ctypes.c_ushort),
        ("bg_inode_bitmap_csum_lo", ctypes.c_ushort),
        ("bg_itable_unused_lo", ctypes.c_ushort),
        ("bg_checksum", ctypes.c_ushort)
    ]

    def __init__(self, filesystem):
        super().__init__()
        self.filesystem = filesystem

    def read_bytes(self, group_number, struct_data):
        fit = min(len(struct_data), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), struct_data, fit)
        self._verify_checksums(struct_data)
        self._verify_checksums(group_number)

    def _verify_checksums(self, group_number):
        data = self.filesystem.UUID
        data += group_number.to_bytes(4, 'little')
        data += bytes(self)[:0x1E]  # FIXME for 64bits structure…
        if self.filesystem.conf.s_feature_ro_compat & Superblock.FeatureRoCompat.RO_COMPAT_METADATA_CSUM != 0 \
                and self.filesystem.conf.s_feature_ro_compat & Superblock.FeatureRoCompat.RO_COMPAT_GDT_CSUM == 0:
            csum = crc32c(data) & 0xFFFF
        elif self.filesystem.conf.s_feature_ro_compat & Superblock.FeatureRoCompat.RO_COMPAT_GDT_CSUM != 0:
            csum = crc16(data)
        else:
            raise FSException("Unknown checksum method")
        if csum != self.bg_checksum:
            raise FSException(f"Wrong checksum in block group descriptor {group_number}")

    # Some accelerators

    def bg_block_bitmap(self):
        return (self.bg_block_bitmap_hi << 32) + self.bg_block_bitmap_lo

    def bg_inode_bitmap(self):
        return (self.bg_inode_bitmap_hi << 32) + self.bg_inode_bitmap_lo

    def bg_inode_table(self):
        if (self.filesystem.conf.s_feature_incompat & self.filesystem.conf.FeatureIncompat.INCOMPAT_64BIT != 0) \
                and self.filesystem.conf.s_desc_size > 32:
            return (self.bg_inode_table_hi << 32) + self.bg_inode_table_lo
        else:
            return self.bg_inode_table_lo


class BlockGroupDescriptor64(BlockGroupDescriptor):
    _fields_ = BlockGroupDescriptor._fields_ + [
        ("bg_block_bitmap_hi", ctypes.c_ulong),
        ("bg_inode_bitmap_hi", ctypes.c_ulong),
        ("bg_inode_table_hi", ctypes.c_ulong),
        ("bg_free_blocks_count_hi", ctypes.c_ushort),
        ("bg_free_inodes_count_hi", ctypes.c_ushort),
        ("bg_used_dirs_count_hi", ctypes.c_ushort),
        ("bg_itable_unused_hi", ctypes.c_ushort),
        ("bg_exclude_bitmap_hi", ctypes.c_ulong),
        ("bg_block_bitmap_csum_hi", ctypes.c_ushort),
        ("bg_inode_bitmap_csum_hi", ctypes.c_ushort),
        ("bg_reserved", ctypes.c_ulong)
    ]


class Inode:
    def __init__(self, filesystem, raw_entry):
        self.filesystem = filesystem
        self._raw_data = raw_entry

    def file_type(self):
        file_type = self.i_mode & 0xF000
        try:
            return self.IMode(file_type)
        except ValueError:
            return file_type

    # Field types

    class IMode(enum.IntEnum):
        # File mode
        S_IXOTH = 0x1  # Others may execute
        S_IWOTH = 0x2  # Others may write
        S_IROTH = 0x4  # Others may read
        S_IXGRP = 0x8  # Group members may execute
        S_IWGRP = 0x10  # Group members may write
        S_IRGRP = 0x20  # Group members may read
        S_IXUSR = 0x40  # Owner may execute
        S_IWUSR = 0x80  # Owner may write
        S_IRUSR = 0x100  # Owner may read
        S_ISVTX = 0x200  # Sticky bit
        S_ISGID = 0x400  # Set GID
        S_ISUID = 0x800  # Set UID

        # These are mutually-exclusive file types:
        S_IFIFO = 0x1000  # FIFO
        S_IFCHR = 0x2000  # Character device
        S_IFDIR = 0x4000  # Directory
        S_IFBLK = 0x6000  # Block device
        S_IFREG = 0x8000  # Regular file
        S_IFLNK = 0xA000  # Symbolic link
        S_IFSOCK = 0xC000  # Socket

    # Fields

    @property
    def i_mode(self):
        """File mode."""
        return int.from_bytes(self._raw_data[0x00:0x00 + 2], 'little')
