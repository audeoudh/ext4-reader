from ext4 import Filesystem


def superblock_dump(filesystem):
    superblock = filesystem.conf
    print(f"Superblock of {filesystem.block_device}")
    fn_size = max(len(fn) for fn, _ in superblock._fields_)
    for field_name, _ in superblock._fields_:
        print(f"  {field_name:{fn_size}}  {getattr(superblock, field_name)!r}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("block_device")
    subparsers = parser.add_subparsers()

    sb_parser = subparsers.add_parser("superblock")
    sb_parser.set_defaults(func=superblock_dump)

    args = parser.parse_args()

    func = args.func
    block_device = args.block_device
    del args.func
    del args.block_device
    with Filesystem(block_device) as filesystem:
        func(filesystem, **vars(args))
