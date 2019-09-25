# Minimalist ext4 implementation in Python

This is a test implementation of ext4 in pure-Python, *not* supporting all ext4
features.  The aim is *not* to write in the ext4 file system, but only to read
*some* (and not all) structure into it.  The supported features are those
required to implement these standard commands:

- `ls [-a] [-l] <path>`
- `cat <path>`

These implementations are in the two scripts `ls.py` and `cat.py`.  To get rid
of difficulties of mounting the file system into the kernel, the project
directly read the block device (`/dev/sdXY`).  This requires the root rights.
You can safely provide your own ext4 file system, as it is never mounted
read-write, but only read-only.  You should provide the device block path while
running scripts:

- `sudo python ls.py /dev/sdXY [-a] [-l] <path>`
- `sudo python cat.py /dev/sdXY <path>`

You may compare with output of the real `ls` and `cat` on a mounted file system.
For the supported features, the output should be the same.
