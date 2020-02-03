from .ext4 import Filesystem
from .data_structures import Inode
FileType = Inode.Mode

__all__ = ['Filesystem', 'FileType']
