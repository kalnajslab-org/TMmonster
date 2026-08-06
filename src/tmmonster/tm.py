import struct
import xmltodict
from datetime import datetime, timezone


def binary_crc(data: bytes, crc: int = 0x1021) -> int:
    '''
    CRC over a TM binary data block, matching the instrument firmware encoder
    (StrateoleXML XMLWriter_v5::writeAndUpdateCRC): 16-bit CRC-CCITT, polynomial
    0x1021, initialised to 0x1021 (reset_crc). The Zephyr spec (STR2-ZEPH-DCI-0-031
    REQ 523) specifies CRC-CCITT over the data block; the firmware transmits it
    MSB-first (big-endian), which is what real TMs contain.
    '''
    for b in data:
        msb = crc >> 8
        lsb = crc & 0xFF
        c = b ^ msb
        c ^= (c >> 4)
        msb = (lsb ^ (c >> 3) ^ (c << 4)) & 0xFF
        lsb = (c ^ (c << 5)) & 0xFF
        crc = (msb << 8) + lsb
    return crc & 0xFFFF


class TMmsg:
    '''
    Base class for Strateole2 TM message decoding.

    See the Zephyr TM specification in:
    ZEPHYR INTERFACES FOR HOSTED INSTRUMENTS
    STR2-ZEPH-DCI-0-031 Version : 1.4

    Binary section framing (REQ 521-524): "START" (5 bytes) + binary data block
    (<Length> bytes, 0-8192 max) + 2-byte CRC (big-endian, over the data block)
    + "END" (3 bytes).
    '''
    def __init__(self, msg_filename: str):
        with open(msg_filename, "rb") as binary_file:
            data = binary_file.read()

        self.data = data
        self.bin_crc_stored = None   # 2-byte CRC that followed the data block
        self.bindata = self.binaryData()
        self.unix_end_time = self.timeStamp()
        date_time = datetime.fromtimestamp(int(self.unix_end_time), tz=timezone.utc)
        self.formatted_time = date_time.strftime("%m/%d/%Y, %H:%M:%S")

    def tm(self):
        '''Return the TM'''
        return self.delimitedText(b'<TM>', b'</TM>')

    def parse_TM_xml(self) -> dict:
        xml_txt = self.delimitedText(b'<TM>', b'</TM>')
        return xmltodict.parse(xml_txt)

    def parse_CRC_xml(self) -> dict:
        xml_txt = self.delimitedText(b'<CRC>', b'</CRC>')
        return xmltodict.parse(xml_txt)

    def delimitedText(self, startTxt: str, endTxt: str) -> str:
        start = self.data.find(startTxt)
        end = self.data.find(endTxt)
        return self.data[start:end+len(endTxt)].decode()

    def binaryData(self) -> bytes:
        tm_xml = self.parse_TM_xml()
        bin_length = int(tm_xml['TM']['Length'])
        bin_start = self.data.find(b'</CRC>\nSTART') + 12
        block = self.data[bin_start:bin_start+bin_length]
        # The 2-byte binary-section CRC follows the data block (big-endian),
        # ahead of the "END" terminator. Kept for optional integrity checking.
        crc_bytes = self.data[bin_start+bin_length:bin_start+bin_length+2]
        if len(crc_bytes) == 2:
            self.bin_crc_stored = int.from_bytes(crc_bytes, 'big')
        return block

    @property
    def bin_crc_valid(self):
        '''
        True/False if the transmitted binary-section CRC matches one computed
        over the data block, or None if there is nothing to check (no payload or
        no stored CRC found).
        '''
        if not self.bindata or self.bin_crc_stored is None:
            return None
        return binary_crc(self.bindata) == self.bin_crc_stored

    def timeStamp(self) -> int:
        return struct.unpack_from('>L', self.bindata, 0)[0]
