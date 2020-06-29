import datetime
import grp
import logging
import pwd

from ext4 import Filesystem, tools
import ext4.files


def main(block_device, path, show_hidden=False, long_format=False):
    with Filesystem(block_device) as filesystem:
        # Obtaining list of files to display
        file = filesystem.get_file(path)
        if isinstance(file, ext4.files.Directory):
            files = list(file.get_files())
            if not show_hidden:
                # Get rid of files starting with .
                files = list(filter(lambda file: not file.filename.startswith("."), files))
        else:
            files = [file]

        # Display
        if not long_format:
            for file in sorted(files, key=lambda file: file.filename.lower()):
                print(file.filename)
        else:
            print(f"total {len(files)}")  # TODO should be number of blocks (?)
            lines = []
            for file in sorted(files, key=lambda file: file.filename.lower()):
                stat = file.get_stat()
                file_type = tools.human_readable_file_type(stat.st_mode)
                rights = tools.human_readable_mode(stat.st_mode)
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime) \
                    .strftime("%Y-%m-%d %H:%M")
                owner = pwd.getpwuid(stat.st_uid).pw_name
                group = grp.getgrgid(stat.st_gid).gr_name
                fname = str(path + ("/" if not path.endswith("/") else "") + file.filename)
                if isinstance(file, ext4.files.SymbolicLink):
                    fname += " -> " + file.get_target()
                lines.append((file_type, rights, str(stat.st_nlink),
                              owner, group, str(stat.st_size), mtime, fname))
            col_length = [max(len(f) for f in fs) for fs in zip(*lines)]
            for line in lines:
                print("{:{}}{:{}} {: >{}} {: >{}} {: >{}} {: >{}} {:{}} {}"
                      .format(*[c for cc in zip(line, col_length) for c in cc]))


def _args_parser():
    import argparse
    parser = argparse.ArgumentParser(prog="ls", description="list directory contents")
    parser.add_argument("block_device",
                        help="Path to the block device containing the ext4 file system")
    parser.add_argument("-a", "--all", action='store_true', dest="show_hidden",
                        help="do not ignore entries starting with .")
    parser.add_argument("-l", action='store_true', dest="long_format",
                        help="use a long listing format")
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="Show debug information")
    parser.add_argument("path", metavar="FILE",
                        help="List information about the FILE")
    return parser


if __name__ == '__main__':
    _parser = _args_parser()
    opts = _parser.parse_args()
    if hasattr(opts, 'verbose'):
        logging.basicConfig(level=logging.INFO if opts.verbose else logging.WARNING)
        del opts.verbose
    main(**vars(opts))
