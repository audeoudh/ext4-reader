import dataclasses
import enum


# Reference: https://ext4.wiki.kernel.org/index.php/Ext4_Disk_Layout#Directory_Entries

class _FileType(enum.IntEnum):
    UNKNOWN = 0x0
    REGULAR_FILE = 0x1
    DIRECTORY = 0x2
    CHARACTER_DEVICE_FILE = 0x2
    BLOCK_DEVICE_FILE = 0x4
    FIFO = 0x5
    SOCKET = 0x6
    SYMBOLIC_LINK = 0x7

    DIR_ENTRY_TAIL = 0xDE


class Directory:
    def __init__(self, block):
        # TODO: parse multiple blocks (long directories)
        self.entries = []
        i = 0
        while i < 4096:
            de = _DirectoryEntry(block, i)
            self.entries.append(de)
            i += de.rec_len


class _DirectoryEntry:
    """Match a `struct ext4_dir_entry_2`."""
    def __init__(self, block, ptr):
        # Pre-load (we do not know the size of the entry).  8 is the minimum entry size
        self._entry_data = block[ptr:ptr + 8]
        # Fetch the true size
        rec_len = self.rec_len
        # Effectively load entry
        self._entry_data = block[ptr:ptr + rec_len]

    @property
    def inode(self):
        return int.from_bytes(self._entry_data[:4], 'little')

    @property
    def rec_len(self):
        return int.from_bytes(self._entry_data[4:6], 'little')

    @property
    def name_len(self):
        return self._entry_data[6]

    @property
    def file_type(self):
        return _FileType(self._entry_data[7])

    @property
    def name(self):
        return self._entry_data[8:8 + self.name_len].decode('utf-8')

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.name}({self.file_type.name})>"


@dataclasses.dataclass
class _InodeTableEntry:
    # i_mode
    # i_uid
    # i_size_lo
    # i_atime
    # i_ctime
    # i_mtime
    # i_dtime
    # i_gid
    # i_links_count
    # i_blocks_lo
    # i_flags
    # osd1
    # i_block
    # i_generation
    # i_file_acl_lo
    # i_size_high
    # i_obso_faddr
    # osd2
    # i_extra_isize
    # i_checksum_high
    # i_ctime_extra
    # i_mtime_extra
    # i_atime_extra
    # i_crtime
    # i_crtime_extra
    # i_version_high
    # i_projid
    pass