#
# See RPUComm/src/RPUcomm.h (class RPURecord) for the bit-packed RPU report
# record format. An RPUREPORT TM payload is simply a block of these records,
# back to back, with no leading header.
#
# Each record is RPU_RECORD_BYTES (38) bytes, big-endian bit order, and is laid
# out as:
#
#   version (4 bits)
#   20 "fast" fields (period = 1, present in every record)   -> 260 bits
#   one 40-bit round-robin "slot" carrying a rotating pair/group of the
#   22 "slow" fields (period = 8), selected by the round_robin_idx fast field
#
# 4 + 260 = 264 bits = 33 bytes (byte-aligned), then 40 bits = 5 bytes for the
# slot, for 38 bytes total. Because both halves are byte-aligned we decode the
# fast fields from payload[0:33] and the slot from payload[33:38].
#
# The slow fields not carried in a given record's slot are left blank.
#

import re
from datetime import datetime, timezone

import bitstruct
from ..tm import TMmsg
from ..csv_util import print_list_csv

RPU_RECORD_BYTES = 38
RPU_RPT_VERSION = 1

# --- Fast fields (period = 1, present in every record) ---------------------
# Includes the leading 4-bit version. 264 bits total = 33 bytes.
rpu_fast_bits = (
    '>'      # big-endian bit order (matches etl::endian::big)
    'u4'     # packet format version
    'u4'     # round_robin_idx
    'u16'    # elapsed_s
    'u16'    # alt (raw m)
    's16'    # lat_delta (signed)
    's16'    # lon_delta (signed)
    'u4'     # sats
    'u4'     # gps_age_s
    'u16'    # opc_d300
    'u16'    # opc_d2000
    'u16'    # tsen_airt
    'u16'    # tsen_pres
    'u16'    # tsen_ptemp
    'u16'    # rs41_air_t
    'u16'    # rs41_pres
    'u16'    # rs41_humidity
    'u16'    # rs41_hsensor_t
    'u10'    # tdlas_mr_avg
    'u12'    # tdlas_bkg
    'u8'     # tdlas_peak
    'u10'    # tdlas_ratio
)

rpu_fast_field_names = [
    'version',
    'round_robin_idx',
    'elapsed_s',
    'alt',
    'lat_delta',
    'lon_delta',
    'sats',
    'gps_age_s',
    'opc_d300',
    'opc_d2000',
    'tsen_airt',
    'tsen_pres',
    'tsen_ptemp',
    'rs41_air_t',
    'rs41_pres',
    'rs41_humidity',
    'rs41_hsensor_t',
    'tdlas_mr_avg',
    'tdlas_bkg',
    'tdlas_peak',
    'tdlas_ratio',
]

# --- Round-robin slow-field slots (period = 8) -----------------------------
# Each slot is 40 bits = 5 bytes. The trailing pad bits (indices 0-5) are
# decoded but discarded.
rpu_slot_bits = {
    0: ('>u16u16u8', ['opc_d500', 'opc_d700', '_pad']),
    1: ('>u16u16u8', ['opc_d1000', 'opc_d2500', '_pad']),
    2: ('>u16u16u8', ['opc_d3000', 'opc_d5000', '_pad']),
    3: ('>u16u16u8', ['rs41_mag_xy', 'bemf_v', '_pad']),
    4: ('>u16u16u8', ['tdlas_spec_1', 'tdlas_spec_2', '_pad']),
    5: ('>u16u16u8', ['tdlas_spec_3', 'tdlas_spec_4', '_pad']),
    6: ('>u8u8u8u8u8', ['tsen_i', 'opc_i', 'pump_i', 'tdlas_i', 'v5']),
    7: ('>u8u8u8u12u4', ['bat_t', 'pump_t', 'pcb_t', 'bat_v', 'heater_stat']),
}

# Every slow field, in round-robin order, for stable CSV columns.
rpu_slow_field_names = [
    'opc_d500', 'opc_d700',
    'opc_d1000', 'opc_d2500',
    'opc_d3000', 'opc_d5000',
    'rs41_mag_xy', 'bemf_v',
    'tdlas_spec_1', 'tdlas_spec_2',
    'tdlas_spec_3', 'tdlas_spec_4',
    'tsen_i', 'opc_i', 'pump_i', 'tdlas_i', 'v5',
    'bat_t', 'pump_t', 'pcb_t', 'bat_v', 'heater_stat',
]

# Per-TM context (not in the binary records): profile number from StateMess2,
# and absolute time/position reconstructed from the per-record deltas plus the
# start reference (epoch/lat/lon) from StateMess3. Blank when not available.
rpu_start_field_names = ['profile', 'tm_time_utc', 'epoch_time', 'lat', 'lon']

# CSV column order: per-TM context first, then round_robin_idx and the rest of
# the fast fields, then all slow fields (only the active slot's fields are
# populated per row).
rpu_csv_field_names = (
    rpu_start_field_names
    + [name for name in rpu_fast_field_names if name != 'version']
    + rpu_slow_field_names
)


def parse_profile(state_mess2):
    '''
    Extract the profile number from a RACHUTS RPUREPORT StateMess2 string,
    e.g. "profile: 2 packet:1 records: 120". Returns an int or None.
    '''
    m = re.search(r'profile:\s*(\d+)', state_mess2 or '')
    return int(m.group(1)) if m else None


def parse_start_values(state_mess3):
    '''
    Extract the (epoch, lat, lon) start reference from a RACHUTS RPUREPORT
    StateMess3 string. Handles both observed forms, e.g.:
        "1781445976, 0.0000, 0.0000, 0.0"
        "PU TM: 2.26, 1781434900, 0.0000, 0.0000, 0.0"
    The epoch is the first integer-valued token >= 1e9; lat and lon are the two
    tokens following it. Returns (epoch, lat, lon) or None if not parseable.
    '''
    nums = [float(t) for t in re.findall(r'-?\d+\.?\d*', state_mess3 or '')]
    for i, n in enumerate(nums):
        if n >= 1e9 and i + 2 < len(nums):
            return int(n), nums[i + 1], nums[i + 2]
    return None


def _scale_fast(raw, start=None):
    '''
    Convert raw fast fields to engineering units (see RPURecord getters).
    If start is a (epoch, lat, lon) tuple, also emit the absolute UTC time and
    lat/lon reconstructed from the per-record deltas.
    '''
    lat_delta = raw['lat_delta'] / 50000.0
    lon_delta = raw['lon_delta'] / 50000.0
    scaled = {}
    if start is not None:
        start_epoch, start_lat, start_lon = start
        epoch_time = start_epoch + raw['elapsed_s']
        scaled['tm_time_utc'] = (
            datetime.fromtimestamp(epoch_time, tz=timezone.utc).isoformat() + 'Z'
        )
        scaled['epoch_time'] = epoch_time
        scaled['lat'] = start_lat + lat_delta
        scaled['lon'] = start_lon + lon_delta
    scaled.update({
        'round_robin_idx': raw['round_robin_idx'],
        'elapsed_s': raw['elapsed_s'],
        'alt': float(raw['alt']),
        'lat_delta': lat_delta,
        'lon_delta': lon_delta,
        'sats': raw['sats'],
        'gps_age_s': raw['gps_age_s'],
        'opc_d300': raw['opc_d300'],
        'opc_d2000': raw['opc_d2000'],
        'tsen_airt': raw['tsen_airt'],
        'tsen_pres': raw['tsen_pres'],
        'tsen_ptemp': raw['tsen_ptemp'],
        'rs41_air_t': (raw['rs41_air_t'] / 100.0) - 100.0,
        'rs41_pres': raw['rs41_pres'] / 10.0,
        'rs41_humidity': raw['rs41_humidity'] / 100.0,
        'rs41_hsensor_t': (raw['rs41_hsensor_t'] / 100.0) - 100.0,
        'tdlas_mr_avg': raw['tdlas_mr_avg'] / 10.0,
        'tdlas_bkg': raw['tdlas_bkg'] / 100.0,
        'tdlas_peak': raw['tdlas_peak'] / 10.0,
        'tdlas_ratio': raw['tdlas_ratio'] / 1000.0,
    })
    return scaled


def _scale_slot(idx, raw):
    '''Convert the active slot's raw slow fields to engineering units.'''
    scaled = {}
    if idx in (0, 1, 2):
        # OPC bin counts pass through unscaled.
        for name in rpu_slot_bits[idx][1]:
            if name != '_pad':
                scaled[name] = raw[name]
    elif idx == 3:
        scaled['rs41_mag_xy'] = raw['rs41_mag_xy'] - 1000
        scaled['bemf_v'] = raw['bemf_v'] / 1000.0
    elif idx in (4, 5):
        # TDLAS spectra pass through unscaled (provisional).
        for name in rpu_slot_bits[idx][1]:
            if name != '_pad':
                scaled[name] = float(raw[name])
    elif idx == 6:
        scaled['tsen_i'] = raw['tsen_i'] * 4.0
        scaled['opc_i'] = raw['opc_i'] * 4.0
        scaled['pump_i'] = raw['pump_i'] * 4.0
        scaled['tdlas_i'] = raw['tdlas_i'] * 4.0
        scaled['v5'] = raw['v5'] / 50.0
    elif idx == 7:
        scaled['bat_t'] = float(raw['bat_t']) - 100.0
        scaled['pump_t'] = float(raw['pump_t']) - 100.0
        scaled['pcb_t'] = float(raw['pcb_t']) - 100.0
        scaled['bat_v'] = raw['bat_v'] / 100.0
        scaled['heater_stat'] = raw['heater_stat']
    return scaled


def csv_header():
    return ','.join(rpu_csv_field_names)


def decode_payload(filename, csv_output, float_format, start=None, profile=None):
    payload = TMmsg(filename).bindata
    num_records = len(payload) // RPU_RECORD_BYTES
    if num_records == 0:
        return

    if start is not None and not csv_output:
        epoch, lat0, lon0 = start
        start_utc = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat() + 'Z'
        print(f'Profile start (UTC): {start_utc}  lat: {lat0}  lon: {lon0}')

    for record_num in range(num_records):
        offset = record_num * RPU_RECORD_BYTES
        record = payload[offset:offset + RPU_RECORD_BYTES]

        version = bitstruct.unpack('>u4', record[:1])[0]
        if version != RPU_RPT_VERSION:
            print(f'Unknown RPUREPORT record version {version} at record {record_num}')
            break

        fast_raw = bitstruct.unpack_dict(rpu_fast_bits, rpu_fast_field_names, record[:33])
        scaled = _scale_fast(fast_raw, start)
        if profile is not None:
            scaled['profile'] = profile

        idx = fast_raw['round_robin_idx']
        slot = rpu_slot_bits.get(idx)
        if slot is None:
            print(f'Unknown round_robin_idx {idx} at record {record_num}')
            break
        slot_fmt, slot_names = slot
        slot_raw = bitstruct.unpack_dict(slot_fmt, slot_names, record[33:38])
        scaled.update(_scale_slot(idx, slot_raw))

        if csv_output:
            csv_values = [scaled.get(field, '') for field in rpu_csv_field_names]
            print_list_csv(csv_values, float_format)
        else:
            float_fmt = f'{{:{float_format}}}' if float_format else None
            print(f'--- RPU record {record_num} of {num_records} (round_robin_idx {idx}) ---')
            for key in rpu_csv_field_names:
                if key not in scaled:
                    continue
                value = scaled[key]
                if key in ('tsen_pres', 'tsen_ptemp'):
                    print(f'{key}: 0x{value:04x}')
                elif isinstance(value, float) and float_fmt:
                    print(f'{key}: {float_fmt.format(value)}')
                else:
                    print(f'{key}: {value}')
            print()
