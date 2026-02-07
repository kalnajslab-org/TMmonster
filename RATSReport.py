import sys
import bitstruct
from RatsBitDefs import *
from RatsScaledVars import *

def decode_payload(payload, header_only):
    header_ver = bitstruct.unpack('>u4', payload[0:1])[0]
    print(f'RATSREPORT header version: {header_ver}')
    if header_ver not in rats_bits:
        print(f'Unknown RATSREPORT header version {header_ver}')
        sys.exit(1)
    header = bitstruct.unpack_dict(rats_bits[header_ver], rats_field_names[header_ver], payload)

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
        return

    # Keep useful header values in variables
    header_size = int(header['header_size_bytes'])
    ecu_record_size = int(header['ecu_record_size_bytes'])

    # Space past the header bytes and get the ECU data records
    ecu_records_bytes = payload[header_size:]
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
        vars = bitstruct.unpack_dict(ecu_bits[ecu_record_ver], ecu_field_names[ecu_record_ver], ecu_record_bytes)

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
