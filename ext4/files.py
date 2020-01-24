import abc
from typing import Optional

from .data_structures import Inode
from .tools import FSException


class File:
    __metaclass__ = abc.ABCMeta

    @classmethod
    def from_path(cls, filesystem, path):
        inode_no = filesystem.locate_file(path)
        inode = filesystem.get_inode(inode_no)
        file_type = inode.file_type()
        try:
            file_type_handler = inode_file_type_handlers[file_type]
        except LookupError:
            raise FSException(f"Unknown file type {file_type} for \"{path}\"") from None
        file = file_type_handler(filesystem, path, inode_no, inode)
        return file

    def __init__(self, filesystem, path, inode_no, inode):
        self.filesystem = filesystem
        self.path = path
        self.inode_no = inode_no
        self.inode = inode

    @property
    def filename(self):
        return self.path.rsplit("/", 1)[1]

    def __repr__(self):
        return f"{self.__class__.__name__}<[{self.inode_no}]:{self.path}>"


class RegularFile(File):
    pass


class Directory(File):
    __metaclass__ = abc.ABCMeta

    def __new__(cls, filesystem, path, inode_no, inode):
        if inode.i_flags & inode.IFlags.EXT4_INDEX_FL != 0:
            return HashTreeDirectory(filesystem, path, inode_no, inode)
        else:
            return LinearDirectory(filesystem, path, inode_no, inode)

    @abc.abstractmethod
    def _get_direntries(self):
        raise NotImplementedError

    def get_files(self) -> [File]:
        for direntry in self._get_direntries():
            full_path = "/".join((self.path, direntry.name))
            inode_no = direntry.inode
            inode = self.filesystem._get_inode(inode_no)
            file = File(self.filesystem, full_path, inode_no, inode)
            yield file

    def _get_direct_subfile(self, path) -> Optional[File]:
        """Non-recursive version of `get_file()`."""
        for direntry in self._get_direntries():
            if direntry.name == path:
                full_path = "/".join((self.path, path))
                inode_no = direntry.inode
                print(f"inode={inode_no}")
                inode = self.filesystem._get_inode(inode_no)
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
                raise NotADirectoryError(self.path + "/" + first_dir)
            if remaining_path == "":
                return subdir
            else:
                return subdir.get_file(remaining_path)


class LinearDirectory(Directory):
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def _get_direntries(self):
        raise NotImplementedError("Linear directories are not supported")


class HashTreeDirectory(Directory):
    def __new__(cls, *args, **kwargs):
        return object.__new__(cls)

    def _get_direntries(self):
        raise NotImplementedError("Hash Tree directories are not supported")


inode_file_type_handlers = {
    Inode.IMode.S_IFDIR: Directory,
    Inode.IMode.S_IFREG: RegularFile,
}
