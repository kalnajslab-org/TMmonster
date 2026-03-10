import struct
import xmltodict
from datetime import datetime, timezone


class TMmsg:
    '''
    Base class for Strateole2 TM message decoding.

    See the Zephyr TM specification in:
    ZEPHYR INTERFACES FOR HOSTED INSTRUMENTS
    STR2-ZEPH-DCI-0-031 Version : 1.3
    '''
    def __init__(self, msg_filename: str):
        with open(msg_filename, "rb") as binary_file:
            data = binary_file.read()

        self.data = data
        self.bindata = self.binaryData()
        self.unix_end_time = self.timeStamp()
        date_time = datetime.fromtimestamp(int(self.unix_end_time), tz=timezone.utc)
        self.formatted_time = date_time.strftime("%m/%d/%Y, %H:%M:%S")

    def tm(self):
        '''Return the TM'''
        return self.delimitedText(b'<TM>', b'</TM>')

    def parse_TM_xml(self) -> str:
        xml_txt = self.delimitedText(b'<TM>', b'</TM>')
        return xmltodict.parse(xml_txt)

    def parse_CRC_xml(self) -> str:
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
        return self.data[bin_start:bin_start+bin_length]

    def timeStamp(self) -> int:
        return struct.unpack_from('>L', self.bindata, 0)[0]
