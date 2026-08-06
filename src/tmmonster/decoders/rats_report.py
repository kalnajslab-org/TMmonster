from datetime import datetime, timezone
import sys
import bitstruct
from ..tm import TMmsg
from ..rats.bit_defs import *
from ..rats.scaled_vars import *
from ..csv_util import print_list_csv

def decode_payload(
    filename: str,
    print_headers: bool,
    print_payload: bool,
    first_file: bool,
    csv_output: bool,
    float_format: str
) -> bool:
    """
    Decode a RATSREPORT TM file. Returns True if this call emitted the CSV
    column header (only happens on the first file that actually contains an
    ECU record), so the dispatcher does not treat a records-less first file as
    having consumed the header slot.
    """
    payload = TMmsg(filename).bindata

    rats_report_ver = bitstruct.unpack('>u4', payload[0:1])[0]
    if rats_report_ver not in rats_bits:
        print(f'Unknown RATSREPORT header version {rats_report_ver}')
        sys.exit(1)
    rats_report_header = bitstruct.unpack_dict(rats_bits[rats_report_ver], rats_field_names[rats_report_ver], payload)

    # Scale them
    scaling_function = globals().get(f'rats_scaled_vars_v{rats_report_ver}', None)
    if scaling_function is None:
        print(f'No scaling function for RATSREPORT header version {rats_report_ver}')
        sys.exit(1)
    scaled_rats_vars = scaling_function(rats_report_header)
    if 'epoch_time' in scaled_rats_vars:
        utc_dt_object = datetime.fromtimestamp(int(scaled_rats_vars['epoch_time']), tz=timezone.utc)
        iso_format_utc = utc_dt_object.isoformat()+'Z'
    else:
        iso_format_utc = None

    if print_headers:
        float_fmt = f'{{:{float_format}}}' if float_format else None
        print(f'RATSREPORT header version: {rats_report_ver}')
        print("----- RATSREPORT binary header:")
        for key, value in scaled_rats_vars.items():
            if isinstance(value, float) and float_fmt:
                print(f'{key}: {float_fmt.format(value)}')
            else:
                print(f'{key}: {value}')
        print()

    if not print_payload:
        return False

    # Whether this call printed the CSV column header (needs a record to know
    # the ECU field names, so a records-less file never emits it).
    header_emitted = False

    # Keep useful header values in variables
    header_size = int(rats_report_header['header_size_bytes'])
    ecu_record_size = int(rats_report_header['ecu_record_size_bytes'])

    # A record may carry an unrecognised version nibble -- e.g. a garbage record
    # that reached RATS over the (best-effort) ECU LoRa link and was passed
    # through by design for diagnostics. Rather than drop it, decode it with the
    # format the report is actually using: the known rev whose packed size
    # matches ecu_record_size (latest if several match). The bogus ecu_id/rev
    # and out-of-range values in the emitted row make the corruption obvious.
    fallback_ver = None
    for v in sorted(ecu_bits):
        if (bitstruct.calcsize(ecu_bits[v]) + 7) // 8 == ecu_record_size:
            fallback_ver = v

    # Space past the header bytes and get the ECU data records
    ecu_records_bytes = payload[header_size:]
    record_num = 0
    offset = 0

    # Unpack the ECU data records
    while offset < len(ecu_records_bytes):
        if offset+ecu_record_size > len(ecu_records_bytes):
            # Fewer than a full record remains: the terminating bytes at the
            # end of the block. A TM whose records overflow the 8192-byte
            # payload cap (Zephyr spec REQ 524) is truncated mid-record, so the
            # last partial record ends up here and is dropped.
            break

        # Get the next record
        ecu_record_bytes = ecu_records_bytes[offset:offset+ecu_record_size]

        # get the ECU record version from the first 4 bits
        ecu_record_ver = bitstruct.unpack('>u4', ecu_record_bytes[:1])[0]
        decode_ver = ecu_record_ver
        if ecu_record_ver not in ecu_bits:
            if fallback_ver is None:
                # No known format matches this record's size; can't decode it.
                print(f'Skipping unknown ECU record version {ecu_record_ver} at record {record_num}',
                      file=sys.stderr)
                record_num += 1
                offset += ecu_record_size
                continue
            # Decode the corrupt record with the report's actual format so a
            # (deliberately bogus) row is still emitted for diagnostics.
            print(f'Corrupt ECU record {record_num}: version {ecu_record_ver}, decoding as v{fallback_ver}',
                  file=sys.stderr)
            decode_ver = fallback_ver

        if first_file and csv_output and record_num == 0:
            csv_col_names = ('tm_time_utc,' if iso_format_utc is not None else '')
            csv_col_names += ','.join(rats_field_names[rats_report_ver])
            csv_col_names += ',' + ','.join(ecu_field_names[decode_ver])
            print(csv_col_names)
            header_emitted = True

        # Unpack the unscaled parameters
        vars = bitstruct.unpack_dict(ecu_bits[decode_ver], ecu_field_names[decode_ver], ecu_record_bytes)

        # Scale them
        scaling_function = globals().get(f'ecu_scaled_vars_v{decode_ver}', None)
        if scaling_function is None:
            print(f'No scaling function for ECU record version {decode_ver} at record {record_num}')
            sys.exit(1)
        scaled_ecu_vars = scaling_function(vars)

        if csv_output:
            csv_values = ([iso_format_utc] if iso_format_utc is not None else [])
            csv_values += [scaled_rats_vars[field] for field in rats_field_names[rats_report_ver]]
            csv_values += [scaled_ecu_vars[field] for field in ecu_field_names[decode_ver]]
            print_list_csv(data=csv_values, float_fmt=float_format)
        else:
            float_fmt = f'{{:{float_format}}}' if float_format else None
            print(f'----- ECU record {record_num}:')
            for key, value in scaled_ecu_vars.items():
                if key in ['tsen_airt', 'tsen_ptemp', 'tsen_pres']:
                    print(f'{key}: 0x{value:06x}')
                elif key in ['gps_date']:
                    print(f'{key}:   {value:06d}')
                elif key in ['gps_time']:
                    print(f'{key}: {value:08d}')
                elif isinstance(value, float) and float_fmt:
                    print(f'{key}: {float_fmt.format(value)}')
                else:
                    print(f'{key}: {value}')
            print()

        record_num += 1

        offset += ecu_record_size

    return header_emitted
