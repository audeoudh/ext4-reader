import enum


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
