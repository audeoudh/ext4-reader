import ctypes

from ext4 import Filesystem


def raw_dump(blob):
    raw_data = bytes(blob)
    l = len(raw_data)
    for i in range((l + 1) // 16):
        print("    0x%02x   " % i, end="")
        for j in range(2):
            for k in range(8):
                print(" %02x" % raw_data[i * 16 + j * 8 + k], end="")
            print("  ", end="")
        print("")


def dump_struct(struct):
    raw_dump(struct)
    fn_size = max(len(fn) for fn, _ in struct._fields_)
    for field_name, type_ in struct._fields_:
        value = getattr(struct, field_name)
        print(f"  {field_name:{fn_size}}[{ctypes.sizeof(type_)}]  {value!r}")


def superblock_dump(filesystem):
    superblock = filesystem.conf
    print(f"Superblock of {filesystem.block_device}")
    dump_struct(superblock)


def block_group_descriptor_dump(filesystem, block_group_no):
    bgd = filesystem.get_block_group_desc(block_group_no)
    print(f"Block group descriptor {block_group_no} of {filesystem.block_device}:")
    print(repr(bytes(bgd)))
    dump_struct(bgd)


def inode_dump(filesystem, inode_no):
    inode = filesystem.get_inode(inode_no)
    print(f"Inode {inode_no} of {filesystem.block_device}:")
    dump_struct(inode)


def block_dump(filesystem, block_no):
    block = filesystem.get_block(block_no)
    print(f"Block number {block_no} of {filesystem.block_device}:")
    raw_dump(block)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("block_device")
    subparsers = parser.add_subparsers()

    sb_parser = subparsers.add_parser("superblock")
    sb_parser.set_defaults(func=superblock_dump)

    bgd_parser = subparsers.add_parser("block_group_descriptor")
    bgd_parser.add_argument("block_group_no", metavar="block_group_number", type=int)
    bgd_parser.set_defaults(func=block_group_descriptor_dump)

    inode_parser = subparsers.add_parser("inode")
    inode_parser.add_argument("inode_no", metavar="inode_number", type=int)
    inode_parser.set_defaults(func=inode_dump)

    block_parser = subparsers.add_parser("block")
    block_parser.add_argument("block_no", metavar="block_number", type=int)
    block_parser.set_defaults(func=block_dump)

    args = parser.parse_args()

    func = args.func
    block_device = args.block_device
    del args.func
    del args.block_device
    with Filesystem(block_device) as filesystem:
        func(filesystem, **vars(args))
