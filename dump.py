# Copyright 2020 Henry-Joseph Audéoud & Timothy Claeys
#
# This file is part of ext4-reader.
#
# ext4-reader is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ext4-reader is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with ext4-reader.  If not, see
# <https://www.gnu.org/licenses/>.

import ctypes
import string

from ext4 import Filesystem
from ext4.files import FileContent, Directory, DirectIndirectFileContent


def _raw_dump(filesystem, blob, offset=0):
    raw_data = bytes(blob)
    l = len(raw_data)
    _my_printables = set(string.ascii_letters + string.punctuation + string.digits)
    for i in range((l + 1) // 16):
        pos = offset + (i * 16)
        block_no = pos // filesystem.conf.get_block_size()
        offset_in_block = pos % filesystem.conf.get_block_size()
        print(f"#{block_no:04X}:{offset_in_block:04X}  ", end="")
        for j in range(2):
            for k in range(8):
                print(" %02x" % raw_data[i * 16 + j * 8 + k], end="")
            print("  ", end="")
        for j in range(2):
            print("  " + "".join(("%c" % c if chr(c) in _my_printables else ".")
                                 for c in raw_data[i * 16 + j * 8:i * 16 + j * 8 + 8]),
                  end="")
        print("")


def _print_table(lines):
    c1s, c2s, c3s = (max(map(len, col)) for col in zip(*lines))
    for c1, c2, c3 in lines:
        print("{c1:{c1s}}  {c2:>{c2s}}  {c3}".format(c1=c1, c2=c2, c3=c3, c1s=c1s, c2s=c2s))


def _dump_struct(struct, **comments):
    lines = []
    fields = [f for k in reversed(struct.__class__.__mro__) if hasattr(k, '_fields_') for f in k._fields_]
    for name, type_ in fields:
        field = getattr(struct.__class__, name)
        value = getattr(struct, name)
        try:
            comment = comments[name]
        except LookupError:
            comment = ""
        if issubclass(type_, ctypes.Array):
            fshex = field.size // len(value) * 2
            value_str = "".join(f"{v:0{fshex}X}" for v in value)
            if len(value_str) > 20:
                value_str = value_str[:12] + ".." + value_str[-6:]
            lines.append((name, value_str, comment))
        elif issubclass(type_, (ctypes.Union, ctypes.Structure)):
            value_type = "UNION" if issubclass(type_, ctypes.Union) else "STRUCT"
            lines.append((name, value_type, comment))
            sub_lines = _dump_struct(value, **comments)
            sub_lines = [("  " + n, v, c) for n, v, c in sub_lines]
            lines.extend(sub_lines)
        else:
            fshex = field.size * 2
            lines.append((name, f"0x{value:0{fshex}X}", comment))
    return lines


def _collect_flags(value, flag_list):
    enabled_flags = []
    for flag in flag_list:
        if value & flag != 0:
            enabled_flags.append(flag.name)
    return "|".join(enabled_flags)


def superblock_dump(filesystem):
    superblock = filesystem.conf
    print(f"Superblock of {filesystem.block_device}")
    compat_flags = _collect_flags(superblock.s_feature_compat, superblock.FeatureCompat)
    incompat_flags = _collect_flags(superblock.s_feature_incompat, superblock.FeatureIncompat)
    ro_compat_flags = _collect_flags(superblock.s_feature_ro_compat, superblock.FeatureRoCompat)
    _print_table(_dump_struct(
        superblock,
        s_feature_compat=compat_flags,
        s_feature_incompat=incompat_flags,
        s_feature_ro_compat=ro_compat_flags,
        s_volume_name="\"" + superblock.get_volume_name() + "\""))
    print("Raw data:")
    _raw_dump(filesystem, superblock)


def block_group_descriptor_dump(filesystem, block_group_no):
    bgd = filesystem.get_block_group_desc(block_group_no, strict=False)
    print(f"Block group descriptor {bgd.no} of {filesystem.block_device} (@0x{bgd.pos:X}):")
    cksum = bgd.verify_checksums()
    flags = _collect_flags(bgd.bg_flags, bgd.Flags)
    _print_table(_dump_struct(
        bgd,
        bg_checksum=("valid" if cksum else "INVALID"),
        bg_flags=flags))
    print("Raw data:")
    _raw_dump(filesystem, bgd, offset=bgd.pos)


def inode_dump(filesystem, inode_no, action='metadata'):
    inode = filesystem.get_inode(inode_no)
    print(f"Inode {inode.no} of {filesystem.block_device} (@0x{inode.pos:X}):")
    if action == 'metadata':
        cksum = inode.verify_checksums()
        mode = _collect_flags(inode.i_mode, list(inode.Mode)[:12])
        for ft in list(inode.Mode)[12:]:
            if (inode.i_mode & 0xF000) == ft:
                mode += f"|{ft.name}"
        flags = _collect_flags(inode.i_flags, inode.Flags)
        _print_table(_dump_struct(
            inode,
            i_checksum_hi=("valid" if cksum else "INVALID"),
            i_flags=flags,
            i_mode=mode))
    elif action == 'blocks':
        file_content = FileContent(filesystem, inode)
        print("Has a " +
              ('direct/indirect' if isinstance(file_content, DirectIndirectFileContent) else 'extent tree') +
              " organized content")
        print("Content block numbers: "
              "[" + ', '.join(f"0x{b_no:X}" for b_no in file_content.get_blocks_no()) + "]")
    elif action == 'content':
        if inode.get_file_type() == inode.Mode.IFDIR:
            print("Is a directory, with entries (names & inodes):")
            dir = Directory(filesystem, "NOT A PATH", inode_no, inode)
            for de in dir._get_direntries():
                print(f"  {de.get_name():16}  {de.inode:> 8X}")


def block_dump(filesystem, block_no):
    block = filesystem.get_block(block_no)
    pos = block_no * filesystem.conf.get_block_size()
    print(f"Block number {block_no} of {filesystem.block_device} (@0x{pos:X}):")
    _raw_dump(filesystem, block, offset=pos)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("block_device")
    subparsers = parser.add_subparsers()

    sb_parser = subparsers.add_parser("superblock")
    sb_parser.set_defaults(func=superblock_dump)

    bgd_parser = subparsers.add_parser("block_group_descriptor")
    bgd_parser.add_argument("block_group_no", metavar="block_group_number", type=lambda x: int(x, 0))
    bgd_parser.set_defaults(func=block_group_descriptor_dump)

    inode_parser = subparsers.add_parser("inode")
    inode_parser.add_argument("inode_no", metavar="inode_number", type=lambda x: int(x, 0))
    inode_parser.add_argument("action", choices=('metadata', 'blocks', 'content'),
                              help="what to dump about the inode", default='metadata')
    inode_parser.set_defaults(func=inode_dump)

    block_parser = subparsers.add_parser("block")
    block_parser.add_argument("block_no", metavar="block_number", type=lambda x: int(x, 0))
    block_parser.set_defaults(func=block_dump)

    args = parser.parse_args()

    func = args.func
    block_device = args.block_device
    del args.func
    del args.block_device
    filesystem = Filesystem(block_device)
    filesystem.fail_on_wrong_checksum = False
    with filesystem:
        func(filesystem, **vars(args))
