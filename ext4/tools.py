import crcmod


class FSException(Exception):
    pass


crc16 = crcmod.mkCrcFun(0x18005)
crc32c = crcmod.mkCrcFun(0x11EDC6F41)


def human_readable_mode(mode):
    """Convert integer-style access rights to string-style notation"""
    sbits = mode >> 9
    u_modes = mode >> 6 & 0o7, mode >> 3 & 0o7, mode & 0o7
    s = ""
    for m, ss, ssf in zip(u_modes, "sst", (0o4, 0o2, 0o1)):
        s += 'r' if m & 0o4 else '-'
        s += 'w' if m & 0o2 else '-'
        if sbits & ssf:
            s += ss if m & 0o1 else ss.upper()
        else:
            s += 'x' if m & 0o1 else '-'
    return s


def human_readable_file_type(mode):
    return "pc?d?b?-?l?s???"[mode & 0o70000 >> 12]


def read_timestamp_ns(i_time, i_time_extra):
    """Read a 32-bits or 64-bits timestamp, as provided in inodes"""
    time = i_time * 1000000000
    if i_time_extra is not None:
        time += (i_time_extra & 0x3 << 32) * 1000000000
        time += i_time_extra >> 2
    return time