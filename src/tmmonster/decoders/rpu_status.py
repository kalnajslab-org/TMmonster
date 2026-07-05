#
# See RPUComm/src/RPUcomm.h (class RPUPacket) and RPUPacket::toJSON() in
# RPUcomm.cpp. An RPUSTATUS TM payload is a single JSON object (raw string
# bytes), already in engineering units, e.g.:
#
#   {"id":"3F74","ver":"dd31ece","state":"STANDBY","wdt_n":8,"buf_rec":0,
#    "vin":15.4,"v5":5.0,"bat_v":12.5,"bat_duty":0,"chg_i":0.1,"bat_t":27.5,
#    "pcb_t":33.0,"pump_i":0,"opc_i":0,"tsen_i":0,"tdlas_i":0,"heater_i":0,
#    "lat":45.710000,"lon":-121.517900,"alt":54.0,"sats":12,
#    "date":140626,"time":20583100}
#
# This decoder parses that JSON and, additionally, decodes the GPS "date"
# (DDMMYY) and "time" (HHMMSSCC) fields into a single UTC ISO timestamp.
#

import json
from datetime import datetime, timezone

from ..tm import TMmsg
from ..csv_util import print_list_csv

# JSON keys, in toJSON() order. A derived "gps_datetime_utc" column is prepended.
rpu_status_field_names = [
    'id', 'ver', 'state', 'wdt_n', 'buf_rec',
    'vin', 'v5', 'bat_v', 'bat_duty', 'chg_i', 'bat_t', 'pcb_t',
    'pump_i', 'opc_i', 'tsen_i', 'tdlas_i', 'heater_i',
    'lat', 'lon', 'alt', 'sats',
    'date', 'time',
]

rpu_status_csv_field_names = ['gps_datetime_utc'] + rpu_status_field_names


def _decode_gps_datetime(date, time):
    '''
    Convert GPS date (DDMMYY, year is 20YY) and time (HHMMSSCC, seconds in
    hundredths) into a UTC ISO timestamp, or None if either is missing/invalid.
    '''
    if not date or not time:
        return None
    dd, mm, yy = date // 10000, (date // 100) % 100, date % 100
    hh = time // 1000000
    mn = (time // 10000) % 100
    ss = (time // 100) % 100
    cc = time % 100
    try:
        dt = datetime(2000 + yy, mm, dd, hh, mn, ss, cc * 10000, tzinfo=timezone.utc)
    except ValueError:
        return None
    return dt.isoformat() + 'Z'


def decode_payload(
    filename: str,
    print_headers: bool,
    print_payload: bool,
    first_file: bool,
    csv_output: bool,
    float_format: str
) -> None:
    payload = TMmsg(filename).bindata
    status = json.loads(payload.decode('utf-8'))
    gps_datetime_utc = _decode_gps_datetime(status.get('date'), status.get('time'))

    if print_headers:
        print('----- RPUSTATUS JSON payload:')
        print(payload.decode('utf-8'))
        print(f'gps_datetime_utc: {gps_datetime_utc}')
        print()

    if not print_payload:
        return

    if csv_output:
        if first_file:
            print(','.join(rpu_status_csv_field_names))
        csv_values = [gps_datetime_utc] + [status.get(field) for field in rpu_status_field_names]
        print_list_csv(data=csv_values, float_fmt=float_format)
    else:
        float_fmt = f'{{:{float_format}}}' if float_format else None
        print(f'gps_datetime_utc: {gps_datetime_utc}')
        for field in rpu_status_field_names:
            value = status.get(field)
            if isinstance(value, float) and float_fmt:
                print(f'{field}: {float_fmt.format(value)}')
            else:
                print(f'{field}: {value}')
        print()
