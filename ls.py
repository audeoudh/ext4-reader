import datetime
import logging

from ext4 import Filesystem, FileType, tools


def main(block_device, path, show_hidden=False, long_format=False):
    with Filesystem(block_device) as filesystem:
        # Obtaining list of files to display
        file = filesystem.get_file(path)
        if file.file_type is FileType.IFDIR:
            dir = file
            files = list(dir.get_files())
            if not show_hidden:
                # Get rid of files starting with .
                files = list(filter(lambda file: not file.filename.startswith("."), files))
        else:
            files = [file]

        # Display
        if long_format:
            print(f"total {len(files)}")  # TODO should be number of blocks (?)
        for file in sorted(files, key=lambda file: file.filename):
            if not long_format:
                print(file.filename)
            else:
                stat = file.get_stat()
                rights = tools.get_string_mode(stat.st_mode)
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                # TODO: dereference symlinks?
                print("{file_type}{rights:9} {nb_links: >2d} {owner: >4d} {group: >4d} {size: >5d} {date} {filename}"
                      .format(file_type='?', rights=rights, nb_links=stat.st_nlink,
                              owner=stat.st_uid, group=stat.st_gid,
                              size=stat.st_size, date=mtime.isoformat(),
                              filename=file.filename))


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
