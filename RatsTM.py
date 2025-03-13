#
# See StratoCore_RATS/src/StratoRats.h for StratoRATS::RATSReportHeader_t,
# which describes the bit-packed TM header block.
#
# See ECUComm/src/ECUComm.h for ECUComm::ECUReport_t, which describes the
# bit-packed ECU data block.
# 
import sys
import xmltodict
from bitstruct import *

# The header section of the RATSReport binary payload
hdr_decode_fmt=('>u8u16u16u1u13')
hdr_field_names = [
    'header_size_bytes', 
    'num_ecu_records', 
    'ecu_record_size_bytes', 
    'ecu_pwr_on', 
    'v56'
]

# The ECU data sections of the RATSReport binary payload
ecu_decode_fmt = (
    '>'    # little-endian
    'u4'   # rev (4 bits)
    'u1'   # heat_on (1 bit)
    'u9'   # v5 (9 bits)
    'u11'  # v12 (11 bits)
    'u13'  # v56 (13 bits)
    'u11'  # board_t (11 bits)
    'u8'   # temp_setpoint (8 bits)
    'u8'   # switch_mA (8 bits)
    'u1'   # gps_valid (1 bit)
    's32'  # gps_lat (32 bits)
    's32'  # gps_lon (32 bits)
    'u16'  # gps_alt (16 bits)
    'u5'   # gps_sats (5 bits)
    'u17'  # gps_date (17 bits)
    'u25'  # gps_time (25 bits)
    'u8'   # gps_age_secs (8 bits)
    'u1'   # rs41_valid (1 bit)
    'u14'  # rs41_airt (14 bits)
    'u10'  # rs41_hum (10 bits)
    'u8'   # rs41_hst (8 bits)
    'u17'  # rs41_pres (17 bits)
    'u1'   # rs41_pcb_h (1 bit)
    'u12'  # tsen_airt (12 bits)
    'u24'  # tsen_ptemp (24 bits)
    'u24'  # tsen_pres (24 bits)
)

ecu_param_names = [
    'rev', 
    'heat_on', 
    'v5', 
    'v12', 
    'v56', 
    'board_t', 
    'temp_setpoint',
    'switch_mA', 
    'gps_valid', 
    'gps_lat', 
    'gps_lon', 
    'gps_alt', 
    'gps_sats', 
    'gps_date', 
    'gps_time', 
    'gps_age_secs', 
    'rs41_valid', 
    'rs41_airt', 
    'rs41_hum', 
    'rs41_hst', 
    'rs41_pres', 
    'rs41_pcb_h', 
    'tsen_airt', 
    'tsen_ptemp', 
    'tsen_pres'
]

if __name__ == "__main__":
    # Open the file
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <TM file>')
        sys.exit(1)
    tm_file = sys.argv[1]

    with open(tm_file, "rb") as tm_file:

        # Read the entire file
        all_bytes = tm_file.read()

        # Find the XML section end
        xml_end = all_bytes.find(b"</TM>")
        if xml_end == -1:        
            print("XML section not found")
            sys.exit(1)
        xml_end += 5
        # Parse the XML section
        xml_str = all_bytes[:xml_end].decode('utf-8')
        xml_dict = xmltodict.parse(xml_str)
        print("----- TM XML section:")
        for key, value in xml_dict['TM'].items():
            print(f'{key}: {value}')
        print()

        if 'RATSReport' not in xml_dict['TM']['StateMess1']:
            print("This is not a RATSReport")
            sys.exit(1)

        # Find the start of the binary payload
        bin_start = all_bytes.find(b"START")+5
        if bin_start == -1:
            print("Binary payload not found")
            sys.exit(1)
        # Unpack the binary header
        header = unpack_dict(hdr_decode_fmt, hdr_field_names, all_bytes[bin_start:])
        header['v56'] = header['v56']/100.0
        print("----- RATSReport binary header:")
        for key, value in header.items():
            print(f'{key}: {value}')
        print()
        
        # Keep useful header values in variables
        header_size = header['header_size_bytes']
        ecu_record_size = header['ecu_record_size_bytes']

        # Space past the header bytes and get the ECU data records
        ecu_records_bytes = all_bytes[bin_start+header_size:]
        record_num = 0
        offset = 0

        # Unpack the ECU data records
        while offset < len(ecu_records_bytes):
            if offset+header_size > len(ecu_records_bytes):
                # We've reached the terminating bytes at the end of the file
                break

            # Get the next record
            ecu_record_bytes = ecu_records_bytes[offset:offset+ecu_record_size]
        
            # Unpack the unscaled parameters
            vars = unpack_dict(ecu_decode_fmt, ecu_param_names, ecu_record_bytes)

            # Scale them
            scaled_vars = {}
            scaled_vars['rev'] = vars['rev']
            scaled_vars['heat_on'] = bool(vars['heat_on'])
            scaled_vars['v5'] = vars['v5']/100.0
            scaled_vars['v12'] = vars['v12']/100.0
            scaled_vars['v56'] = vars['v56']/100.0
            scaled_vars['board_t'] = vars['board_t']/10.0-100.0
            scaled_vars['temp_setpoint'] = vars['temp_setpoint']-100.0
            scaled_vars['switch_mA'] = vars['switch_mA']
            scaled_vars['gps_valid'] = bool(vars['gps_valid'])
            scaled_vars['gps_lat'] = vars['gps_lat']*1.0e-6
            scaled_vars['gps_lon'] = vars['gps_lon']*1.0e-6
            scaled_vars['gps_alt'] = vars['gps_alt']*1.0
            scaled_vars['gps_sats'] = vars['gps_sats']
            scaled_vars['gps_date'] = vars['gps_date']
            scaled_vars['gps_time'] = vars['gps_time']
            scaled_vars['gps_age_secs'] = vars['gps_age_secs']
            scaled_vars['rs41_valid'] = bool(vars['rs41_valid'])
            scaled_vars['rs41_airt'] = vars['rs41_airt']/100.0-100.0
            scaled_vars['rs41_hum'] = vars['rs41_hum']/100.0
            scaled_vars['rs41_hst'] = vars['rs41_hst']
            scaled_vars['rs41_pres'] = vars['rs41_pres']/100.0
            scaled_vars['rs41_pcb_h'] = bool(vars['rs41_pcb_h'])
            scaled_vars['tsen_airt'] = vars['tsen_airt']
            scaled_vars['tsen_ptemp'] = vars['tsen_ptemp']
            scaled_vars['tsen_pres'] = vars['tsen_pres']

            print(f'----- ECU record {record_num}:')
            for key, value in scaled_vars.items():
                if key in ['tsen_airt', 'tsen_ptemp', 'tsen_pres']:
                    print(f'{key}: 0x{value:06x}')
                elif key in ['gps_date']:
                    print(f'{key}:   {value:06d}')
                elif key in ['gps_time']:
                    print(f'{key}: {value:08d}')
                else:
                    print(f'{key}: {value}')
            print()
            record_num += 1

            offset += ecu_record_size
