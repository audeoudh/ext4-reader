from ext4 import Filesystem

def superblock_dump(filesystem):
    superblock = filesystem.conf
    print(f"Superblock of {filesystem.block_device}")
    fn_size = max(len(fn) for fn, _ in superblock._fields_)
    for field_name, _ in superblock._fields_:
        print(f"  {field_name:{fn_size}}  {getattr(superblock, field_name)!r}")


def block_group_descriptor_dump(filesystem, block_group_number):
    bgd = filesystem.get_block_group_desc(block_group_number)
    print(f"Block group descriptor {block_group_number} of {filesystem.block_device}:")
    fn_size = max(len(fn) for fn, _ in bgd._fields_)
    for field_name, _ in bgd._fields_:
        print(f"  {field_name:{fn_size}}  {getattr(bgd, field_name)!r}")


def inode_dump(filesystem, inode_no):
    inode = filesystem.get_inode(inode_no)
    print(f"Inode {inode_no} of {filesystem.block_device}:")
    fn_size = max(len(fn) for fn, _ in inode._fields_)
    for field_name, _ in inode._fields_:
        print(f"  {field_name:{fn_size}}  {getattr(inode, field_name)!r}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("block_device")
    subparsers = parser.add_subparsers()

    sb_parser = subparsers.add_parser("superblock")
    sb_parser.set_defaults(func=superblock_dump)

    bgd_parser = subparsers.add_parser("block_group_descriptor")
    bgd_parser.add_argument("block_group_number", type=int)
    bgd_parser.set_defaults(func=block_group_descriptor_dump)

    inode_parser = subparsers.add_parser("inode")
    inode_parser.add_argument("inode_no", metavar="inode_number", type=int)
    inode_parser.set_defaults(func=inode_dump)

    args = parser.parse_args()

    func = args.func
    block_device = args.block_device
    del args.func
    del args.block_device
    with Filesystem(block_device) as filesystem:
        func(filesystem, **vars(args))
