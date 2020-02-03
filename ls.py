from ext4 import Filesystem, FileType


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
                print("{rights:10} {nb_links} {owner} {group} {size} {date} {filename}"
                      .format(rights="?", nb_links=5, owner=1000, group=1000,
                              size=1000, date="?????", filename=file.filename))


def _args_parser():
    import argparse
    parser = argparse.ArgumentParser(prog="ls", description="list directory contents")
    parser.add_argument("block_device",
                        help="Path to the block device containing the ext4 file system")
    parser.add_argument("-a", "--all", action='store_true', dest="show_hidden",
                        help="do not ignore entries starting with .")
    parser.add_argument("-l", action='store_true', dest="long_format",
                        help="use a long listing format")
    parser.add_argument("path", metavar="FILE",
                        help="List information about the FILE")
    return parser


if __name__ == '__main__':
    _parser = _args_parser()
    opts = _parser.parse_args()
    main(**vars(opts))
