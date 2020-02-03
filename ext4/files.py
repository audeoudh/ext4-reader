import abc
from typing import Optional, Iterator

from .data_structures import Inode, ExtentHeader, ExtentIdx, Extent, DirEntry, DirEntry2, Superblock
from .tools import FSException


class File:
    __metaclass__ = abc.ABCMeta

    def __new__(cls, filesystem, path, inode_no, inode: Inode):
        if cls is File:
            # Build a subclass of this abstract class
            file_type = inode.get_file_type()
            if file_type == Inode.Mode.IFIFO:
                return Fifo.__new__(Fifo, filesystem, path, inode_no, inode)
            elif file_type == Inode.Mode.IFCHR:
                return CharDevice.__new__(CharDevice, filesystem, path, inode_no, inode)
            elif file_type == Inode.Mode.IFDIR:
                return Directory.__new__(Directory, filesystem, path, inode_no, inode)
            elif file_type == Inode.Mode.IFBLK:
                return BlockDevice.__new__(BlockDevice, filesystem, path, inode_no, inode)
            elif file_type == Inode.Mode.IFREG:
                return RegularFile.__new__(RegularFile, filesystem, path, inode_no, inode)
            elif file_type == Inode.Mode.IFLNK:
                return SymbolicLink.__new__(SymbolicLink, filesystem, path, inode_no, inode)
            elif file_type == Inode.Mode.IFSOCK:
                return Socket.__new__(Socket, filesystem, path, inode_no, inode)
            else:
                raise FSException(f"Unknown file type 0x{file_type:X} for \"{path}\"")
        else:
            # Instanciate a subclass, OK
            return super().__new__(cls)

    def __init__(self, filesystem, path, inode_no, inode: Inode):
        self.filesystem = filesystem
        self.path = path
        self.inode_no = inode_no
        self.inode = inode
        self.content = FileContent(self.filesystem, inode)

    @property
    @abc.abstractmethod
    def file_type(self):
        raise NotImplementedError

    @property
    def filename(self):
        return self.path.rsplit("/", 1)[1]

    def __repr__(self):
        return f"{self.__class__.__name__}<[{self.inode_no}]:{self.path}>"


class Fifo(File):
    def __init__(self, filesystem, path, inode_no, inode: Inode):
        super().__init__(filesystem, path, inode_no, inode)
        raise NotImplementedError

    @property
    def file_type(self):
        return Inode.Mode.IFIFO


class CharDevice(File):
    def __init__(self, filesystem, path, inode_no, inode: Inode):
        super().__init__(filesystem, path, inode_no, inode)
        raise NotImplementedError

    @property
    def file_type(self):
        return Inode.Mode.IFCHR


class Directory(File):
    __metaclass__ = abc.ABCMeta

    def __new__(cls, filesystem, path, inode_no, inode):
        if cls is Directory:
            # Build a subclass of this abstract class
            if inode.i_flags & inode.Flags.INDEX != 0:
                return HashTreeDirectory(filesystem, path, inode_no, inode)
            else:
                return LinearDirectory(filesystem, path, inode_no, inode)
        else:
            # Instanciate a subclass, OK
            return super().__new__(cls, filesystem, path, inode_no, inode)

    @property
    def file_type(self):
        return Inode.Mode.IFDIR

    @abc.abstractmethod
    def _get_direntries(self) -> Iterator[DirEntry]:
        raise NotImplementedError

    def get_files(self) -> [File]:
        for direntry in self._get_direntries():
            full_path = "/".join((self.path, direntry.get_name()))
            inode_no = direntry.inode
            inode = self.filesystem.get_inode(inode_no)
            file = File(self.filesystem, full_path, inode_no, inode)
            yield file

    def _get_direct_subfile(self, path) -> Optional[File]:
        """Non-recursive version of `get_file()`."""
        for direntry in self._get_direntries():
            if direntry.get_name() == path:
                full_path = "/".join((self.path, path))
                inode_no = direntry.inode
                inode = self.filesystem.get_inode(inode_no)
                return File(self.filesystem, full_path, inode_no, inode)
        print(f"{path=}")
        raise FileNotFoundError(path) from None

    def get_file(self, path):
        """Dereference successive directories along the path and return the
        inode number of the last component of the path"""
        if path.startswith("/"):
            return self.filesystem.get_file(path)
        try:
            first_dir, remaining_path = path.split("/", 1)
        except ValueError:
            # No / in path, directly load and return the corresponding file
            subfile = self._get_direct_subfile(path)
            return subfile
        else:
            # At least one "/" in path.  Forward the work to the first subdir
            subdir = self._get_direct_subfile(first_dir)
            if not isinstance(subdir, Directory):
                raise NotADirectoryError(f"{self.path}/{first_dir}")
            if remaining_path == "":
                return subdir
            else:
                return subdir.get_file(remaining_path)


class LinearDirectory(Directory):
    def _get_direntries(self) -> [DirEntry]:
        for block in self.content.get_blocks():
            i = 0
            while i < 4096:
                if not self.filesystem.conf.has_flag(Superblock.FeatureIncompat.INCOMPAT_FILETYPE):
                    de = DirEntry().read_bytes(block[i:])
                else:
                    de = DirEntry2().read_bytes(block[i:])
                if de.inode == 0:
                    # End of the entry
                    break
                yield de
                i += de.rec_len


class HashTreeDirectory(Directory):
    def _get_direntries(self) -> Iterator[DirEntry]:
        raise NotImplementedError("Hash Tree directories are not supported")


class BlockDevice(File):
    def __init__(self, filesystem, path, inode_no, inode: Inode):
        super().__init__(filesystem, path, inode_no, inode)
        raise NotImplementedError

    @property
    def file_type(self):
        return Inode.Mode.IFBLK


class RegularFile(File):
    @property
    def file_type(self):
        return Inode.Mode.IFREG


class SymbolicLink(File):
    @property
    def file_type(self):
        return Inode.Mode.IFLNK


class Socket(File):
    def __init__(self, filesystem, path, inode_no, inode: Inode):
        super().__init__(filesystem, path, inode_no, inode)
        raise NotImplementedError

    @property
    def file_type(self):
        return Inode.Mode.IFSOCK


class FileContent:
    __metaclass__ = abc.ABCMeta

    def __new__(cls, filesystem, inode: Inode):
        if cls is FileContent:
            # Build a subclass of this abstract class
            if inode.i_flags & inode.Flags.EXTENTS != 0:
                return ExtentTreeFileContent.__new__(ExtentTreeFileContent, filesystem, inode)
            elif inode.i_flags & inode.Flags.INLINE_DATA != 0:
                raise NotImplementedError("Inline data are not supported")
            else:
                return DirectIndirectFileContent.__new__(DirectIndirectFileContent, filesystem, inode)
        else:
            # Instanciating a subclass, OK.
            return super().__new__(cls)

    def __init__(self, filesystem, inode: Inode):
        self.filesystem = filesystem
        self.inode = inode

    @abc.abstractmethod
    def get_blocks_no(self) -> Iterator[int]:
        raise NotImplementedError

    def get_blocks(self) -> Iterator[bytes]:
        for block_no in self.get_blocks_no():
            yield self.filesystem.get_block(block_no)


class DirectIndirectFileContent(FileContent):
    def get_blocks_no(self):
        for offset in range(12):
            block_address = int.from_bytes(bytes(self.inode.i_block)[offset * 4:(offset + 1) * 4], 'little')
            if block_address == 0:
                break
            else:
                yield block_address
        else:
            raise NotImplementedError("Indirect block addressing is not supported")


class ExtentTreeFileContent(FileContent):
    def __init__(self, filesystem, inode, strict=True):
        super().__init__(filesystem, inode)
        if strict:
            ExtentHeader().read_bytes(self.inode.i_block, strict=strict)

    def get_blocks_no(self):
        header = ExtentHeader().read_bytes(self.inode.i_block)
        if header.eh_depth != 0:
            # Index block locations are here
            idx_blocks = (ExtentIdx(self.inode.i_block[i * 12:(i + 1) * 12]) for i in range(header.eh_entries))
            raise NotImplementedError("Deep extent trees are not supported")
        else:
            # Data block locations are here
            for i in range(header.eh_entries):
                ee = Extent().read_bytes(bytes(self.inode.i_block)[(i + 1) * 12:(i + 2) * 12])
                if ee.ee_len > 32768:
                    raise NotImplementedError("Uninitialized extents are not supported")
                start = ee.get_start()
                for i_block in range(ee.ee_len):
                    yield start + i_block
