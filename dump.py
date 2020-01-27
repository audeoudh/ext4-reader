import ctypes

import ext4.tools
from ext4 import Filesystem


def _raw_dump(filesystem, blob, offset=0):
    raw_data = bytes(blob)
    l = len(raw_data)
    for i in range((l + 1) // 16):
        pos = offset + (i * 16)
        block_no = pos // filesystem.conf.get_block_size()
        offset_in_block = pos % filesystem.conf.get_block_size()
        print(f"#{block_no:04X}:{offset_in_block:04X}  ", end="")
        for j in range(2):
            for k in range(8):
                print(" %02x" % raw_data[i * 16 + j * 8 + k], end="")
            print("  ", end="")
        print("")


def _dump_struct(struct, **comments):
    lines = []
    for name, type_ in struct._fields_:
        field = getattr(struct.__class__, name)
        value = getattr(struct, name)
        if issubclass(type_, ctypes.Array):
            fshex = field.size // len(value) * 2
            value_str = " ".join(f"{v:0{fshex}X}" for v in value)
            if len(value_str) > 20:
                value_str = value_str[:13] + "..." + value_str[-4:]
        else:
            fshex = field.size * 2
            value_str = f"0x{value:0{fshex}X}"
        try:
            comment = comments[name]
        except LookupError:
            comment = ""
        lines.append((name, value_str, comment))
    c1s, c2s, c3s = (max(map(len, col)) for col in zip(*lines))
    for c1, c2, c3 in lines:
        print("{c1:{c1s}} {c2:>{c2s}} {c3}".format(c1=c1, c2=c2, c3=c3, c1s=c1s, c2s=c2s))


def _collect_flags(value, flag_list):
    enabled_flags = []
    for flag in flag_list:
        if value & flag != 0:
            enabled_flags.append(flag.name)
    return "|".join(enabled_flags)


def superblock_dump(filesystem):
    superblock = filesystem.conf
    print(f"Superblock of {filesystem.block_device}")
    ro_compat_flags = _collect_flags(superblock.s_feature_ro_compat, superblock.FeatureRoCompat)
    incompat_flags = _collect_flags(superblock.s_feature_incompat, superblock.FeatureIncompat)
    _dump_struct(superblock,
                 s_freature_ro_compat=ro_compat_flags,
                 s_feature_incompat=incompat_flags,
                 s_volume_name="\"" + superblock.get_volume_name() + "\"")
    print("Raw data:")
    _raw_dump(filesystem, superblock)


def block_group_descriptor_dump(filesystem, block_group_no):
    bgd = filesystem.get_block_group_desc(block_group_no)
    print(f"Block group descriptor {bgd.no} of {filesystem.block_device} (@{bgd.pos}):")
    try:
        bgd._verify_checksums(block_group_no)
        cksum = True
    except ext4.tools.FSException:
        cksum = False
    flags = _collect_flags(bgd.bg_flags, bgd.Flags)
    _dump_struct(bgd,
                 bg_checksum=("ok" if cksum else "KO!"),
                 bg_flags=flags)
    print("Raw data:")
    _raw_dump(filesystem, bgd, offset=filesystem._get_block_group_desc_pos(block_group_no))


def inode_dump(filesystem, inode_no):
    inode = filesystem.get_inode(inode_no)
    print(f"Inode {inode.no} of {filesystem.block_device} (@{inode.pos}):")
    _dump_struct(inode)


def block_dump(filesystem, block_no):
    block = filesystem.get_block(block_no)
    pos = block_no * filesystem.conf.get_block_size()
    print(f"Block number {block_no} of {filesystem.block_device} (@{pos}):")
    _raw_dump(filesystem, block, offset=pos)


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
