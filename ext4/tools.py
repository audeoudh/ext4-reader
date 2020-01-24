import crcmod


class FSException(Exception):
    pass


crc16 = crcmod.mkCrcFun(0x18005, 0xffff, True)
crc32c = crcmod.mkCrcFun(0x11EDC6F41, 0xffff, True)
