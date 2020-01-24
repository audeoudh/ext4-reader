import crcmod


class FSException(Exception):
    pass


crc32c = crcmod.mkCrcFun(0x11EDC6F41, 0xffff, True)
