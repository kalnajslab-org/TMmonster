#
# See StratoCore_RATS/src/RATSReport.h which describes the bit-packed 
# RATSReport header block.
#
# See ECUComm/src/ECUComm.h for ECUComm::ECUReport_t, which describes the
# bit-packed ECU data block.
# 

import sys
import bitstruct
import xmltodict
from bitstruct import unpack_dict
import argparse
from RatsBitDefs import *
from RatsScaledVars import *

# The RATSReport contains a bit-packed RATSReport header and a series of ECUReports.
#
# The RATSReport and ECUReports have revision numbers, which are stored in the first 4 bits of the record.

# The general scheme for unpacking the bit packed data for the RATSReport and ECUReports 
# is the same, and utilize the bitstruct library.
#
# A "*_bits" dictionary is defined for each version of the RATSReport and ECUReport. These
# correspond to the C structures defined the C++ header files. When a new version is added,
# add a new entry to the "_bits" dictionary with the bitstruct format string for that version.
# The format strings are defined in RatsBitDefs.py.
#
# Similarly, a "*_field_names" dictionary is defined for each version of the RATSReport and ECUReport.
# These correspond to the field names in the C++ header files. When a new version is added, 
# add a new entry to the "_field_names" dictionary with the field names for that version.
# The field name lists are defined in RatsBitDefs.py.
#
# Finally, scaling functions "*_scaled_vars_v<rev>" are defined for each version of the RATSReport and ECUReport.
# These functions take the raw data unpacked from the bit-packed format and scale it to human-readable units.
# The scaling functions are defined in RatsScaledVars.py.

def parse_args():
    parser = argparse.ArgumentParser(description="Decode RATS TM binary files.")
    parser.add_argument("tm_file", nargs='+', help="Path(s) to the TM file(s)")
    parser.add_argument("--header-only", action="store_true", help="Print only the RATSREPORT header")
    return parser.parse_args()

def main(args):
    header_only = args.header_only
    tm_files = args.tm_file if isinstance(args.tm_file, list) else [args.tm_file]

    for tm_file in tm_files:
        print(f"Processing file: {tm_file}")

        with open(tm_file, "rb") as tm_file:

            # Read the entire file
            all_bytes = tm_file.read()

            # Find the XML section end
            # Find the XML section start
            xml_start = all_bytes.find(b"<TM>")
            if xml_start == -1:
                print("XML section start not found")
            xml_end = all_bytes.find(b"</TM>")
            if xml_end == -1:        
                print("XML section not found")
            if xml_end == -1 or xml_start == -1:
                continue
            xml_end += 5  # include the </TM> tag
            # Parse the XML section
            xml_str = all_bytes[xml_start:xml_end].decode('utf-8')
            xml_dict = xmltodict.parse(xml_str)
            print("----- TM XML section:")
            for key, value in xml_dict['TM'].items():
                print(f'{key}: {value}')
            print()

            if any(key in xml_dict['TM']['StateMess1'] for key in ['RATSReport', 'RATSREPORT']):
                # Find the start of the binary payload
                bin_start = all_bytes.find(b"START")+5
                if bin_start == -1:
                    print("Binary payload not found")
                    sys.exit(1)
                # Unpack the binary header
                header_ver = bitstruct.unpack('>u4', all_bytes[bin_start:bin_start+1])[0]
                print(f'RATSREPORT header version: {header_ver}')
                if header_ver not in rats_bits:
                    print(f'Unknown RATSREPORT header version {header_ver}')
                    sys.exit(1)
                header = unpack_dict(rats_bits[header_ver], rats_field_names[header_ver], all_bytes[bin_start:])

                # Scale them
                scaling_function = globals().get(f'rats_scaled_vars_v{header_ver}', None)
                if scaling_function is None:
                    print(f'No scaling function for RATSREPORT header version {header_ver}')
                    sys.exit(1)
                scaled_rats_vars = scaling_function(header)

                print("----- RATSREPORT binary header:")
                for key, value in scaled_rats_vars.items():
                    print(f'{key}: {value}')
                print()
                
                if header_only:
                    continue

                # Keep useful header values in variables
                header_size = int(header['header_size_bytes'])
                ecu_record_size = int(header['ecu_record_size_bytes'])

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
                
                    # get the ECU record version from the first 4 bits
                    ecu_record_ver = bitstruct.unpack('>u4', ecu_record_bytes[:1])[0]
                    if ecu_record_ver not in ecu_bits:
                        print(f'Unknown ECU record version {ecu_record_ver} at record {record_num}')
                        break

                    # Unpack the unscaled parameters
                    vars = unpack_dict(ecu_bits[ecu_record_ver], ecu_field_names[ecu_record_ver], ecu_record_bytes)

                    # Scale them
                    scaling_function = globals().get(f'ecu_scaled_vars_v{ecu_record_ver}', None)
                    if scaling_function is None:
                        print(f'No scaling function for ECU record version {ecu_record_ver} at record {record_num}')
                        sys.exit(1)
                    scaled_ecu_vars = scaling_function(vars)

                    print(f'----- ECU record {record_num}:')
                    for key, value in scaled_ecu_vars.items():
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
            else:
                print("No RATSREPORT section found in TM XML")

if __name__ == "__main__":
    args = parse_args()
    main(args)