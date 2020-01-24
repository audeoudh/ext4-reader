import ctypes
import enum

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
        ("s_volume_name", ctypes.c_char * 16),
        ("s_last_mounted", ctypes.c_char * 64),
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

    def has_flag(self, flag):
        if isinstance(flag, self.FeatureIncompat):
            return self.s_feature_incompat & flag != 0
        elif isinstance(flag, self.FeatureRoCompat):
            return self.s_feature_ro_compat & flag != 0
        else:
            raise FSException(f"Unknown flag {flag}")

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

    def __init__(self, filesystem):
        super().__init__()
        self.filesystem = filesystem

    def read_bytes(self, group_number, struct_data):
        fit = min(len(struct_data), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), struct_data, fit)
        self._verify_checksums(group_number)
        return self

    def _verify_checksums(self, group_number):
        data = bytes(self.filesystem.UUID)
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

    def get_inode_table_loc(self):
        return self.bg_inode_table_lo


class BlockGroupDescriptor64(BlockGroupDescriptor):
    _fields_ = BlockGroupDescriptor._fields_ + [
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

    def get_inode_table_loc(self):
        return (self.bg_inode_table_hi << 32) + self.bg_inode_table_lo


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
        ("i_osd1", ctypes.c_uint8 * 4),
        ("i_block", ctypes.c_uint8 * 60),
        ("i_generation", ctypes.c_uint32),
        ("i_file_acl_lo", ctypes.c_uint32),
        ("i_size_high", ctypes.c_uint32),  # i_dir_acl in ext2/3
        ("i_obso_faddr", ctypes.c_uint32),
        ("i_osd2", ctypes.c_uint8 * 12),
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

    def __init__(self, filesystem):
        super().__init__()
        self.filesystem = filesystem

    def read_bytes(self, inode_no, struct_data):
        fit = min(len(struct_data), ctypes.sizeof(self))
        ctypes.memmove(ctypes.addressof(self), struct_data, fit)
        self._verify_checksums(inode_no, struct_data)
        return self

    def _verify_checksums(self, inode_no, struct_data):
        # FIXME, not sure about calculation
        if self.filesystem.conf.has_flag(Superblock.FeatureRoCompat.RO_COMPAT_METADATA_CSUM):
            data = bytes(self.filesystem.UUID)
            if self.filesystem.conf.has_flag(Superblock.FeatureIncompat.INCOMPAT_64BIT):
                data += inode_no.to_bytes(8, 'little')
            else:
                data += inode_no.to_bytes(4, 'little')
            data += struct_data[:0x82] + b"\x00\x00" + struct_data[0x84:]
            csum = crc32c(data)
            if (csum & 0xFFFF0000) >> 16 != self.i_checksum_hi:
                raise FSException(f"Wrong checksum in inode {inode_no}")

    # Some accelerators

    def file_type(self):
        file_type = self.i_mode & 0xF000
        try:
            return self.IMode(file_type)
        except ValueError:
            raise FSException(f"Unknwon file type {file_type}") from None

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

    class IFlags(enum.IntEnum):
        EXT4_SECRM_FL = 0x1
        EXT4_UNRM_FL = 0x2
        EXT4_COMPR_FL = 0x4
        EXT4_SYNC_FL = 0x8
        EXT4_IMMUTABLE_FL = 0x10
        EXT4_APPEND_FL = 0x20
        EXT4_NODUMP_FL = 0x40
        EXT4_NOATIME_FL = 0x80
        EXT4_DIRTY_FL = 0x100
        EXT4_COMPRBLK_FL = 0x200
        EXT4_NOCOMPR_FL = 0x400
        EXT4_ENCRYPT_FL = 0x800
        EXT4_INDEX_FL = 0x1000
        EXT4_IMAGIC_FL = 0x2000
        EXT4_JOURNAL_DATA_FL = 0x4000
        EXT4_NOTAIL_FL = 0x8000
        EXT4_DIRSYNC_FL = 0x10000
        EXT4_TOPDIR_FL = 0x20000
        EXT4_HUGE_FILE_FL = 0x40000
        EXT4_EXTENTS_FL = 0x80000
        EXT4_EA_INODE_FL = 0x200000
        EXT4_EOFBLOCKS_FL = 0x400000
        EXT4_SNAPFILE_FL = 0x01000000
        EXT4_SNAPFILE_DELETED_FL = 0x04000000
        EXT4_SNAPFILE_SHRUNK_FL = 0x08000000
        EXT4_INLINE_DATA_FL = 0x10000000
        EXT4_PROJINHERIT_FL = 0x20000000
        EXT4_RESERVED_FL = 0x80000000
    # Fields

    @property
    def i_mode(self):
        """File mode."""
        return int.from_bytes(self._raw_data[0x00:0x00 + 2], 'little')
