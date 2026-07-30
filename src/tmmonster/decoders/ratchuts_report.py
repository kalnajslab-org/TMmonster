#
# See StratoRatchuts::SendRATCHUTSREPORT(). A RATCHUTSREPORT TM payload is a
# JSON object wrapping a "ratchuts" header (always present) and, when an RPU
# status is available, an "rpu" block carrying the decoded RPU status -- the
# same fields the legacy RPUSTATUS TM sent (RPUPacket::toJSON()):
#
#   {"ratchuts":{"epoch":1785414236,"mode":"FL","substate":2,"reel":0.00,
#                "src":"LORA","rpu_age_s":59},
#    "rpu":{"id":"3F74","ver":"...","state":"MEASURE",...,"date":...,"time":...}}
#
# "epoch" is system time in seconds since 1970 (same as the RATSREPORT header
# epoch; 0/unset until the RTC is set from GPS). A header-only report (no "rpu"
# block) means no RPU status was available; its rpu columns are left blank.
#

import json
from datetime import datetime, timezone

from ..tm import TMmsg
from ..csv_util import print_list_csv

# Fields of the nested "rpu" block, in RPUPacket::toJSON() order (RPUcomm.cpp).
rpu_status_field_names = [
    'id', 'ver', 'state', 'wdt_n', 'buf_rec',
    'vin', 'v5', 'bat_v', 'bat_duty', 'chg_i', 'bat_t', 'pcb_t',
    'pump_i', 'opc_i', 'tsen_i', 'tdlas_i', 'heater_i',
    'lat', 'lon', 'alt', 'sats',
    'date', 'time',
]

# "ratchuts" header fields for display/CSV. Raw JSON keys are epoch, mode,
# substate, reel, src, rpu_age_s (firmware order); epoch_utc is derived here.
ratchuts_header_field_names = ['epoch', 'epoch_utc', 'mode', 'substate', 'reel', 'src', 'rpu_age_s']

# CSV columns: ratchuts header, then the GPS time derived from the rpu block,
# then the rpu block's own fields.
ratchuts_report_csv_field_names = (
    ratchuts_header_field_names + ['gps_datetime_utc'] + rpu_status_field_names
)


def _epoch_to_utc(epoch):
    '''Convert a unix epoch (seconds) to a UTC ISO timestamp, or None if unset/invalid.'''
    if not epoch:
        return None
    try:
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).isoformat() + 'Z'
    except (ValueError, OverflowError, OSError):
        return None


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
    # Firmware can emit non-UTF-8 bytes inside a string field (e.g. a corrupt
    # "ver"); decode with replacement so one bad field doesn't drop the record.
    json_text = payload.decode('utf-8', errors='replace')
    report = json.loads(json_text)

    header = report.get('ratchuts', {})
    rpu = report.get('rpu')  # None on header-only reports
    epoch_utc = _epoch_to_utc(header.get('epoch'))
    gps_datetime_utc = (
        _decode_gps_datetime(rpu.get('date'), rpu.get('time')) if rpu else None
    )

    if print_headers:
        print('----- RATCHUTSREPORT JSON payload:')
        print(json_text)
        print(f'epoch_utc: {epoch_utc}')
        print(f'gps_datetime_utc: {gps_datetime_utc}')
        print()

    if not print_payload:
        return

    float_fmt = f'{{:{float_format}}}' if float_format else None

    # Merge header, derived timestamps, and (if present) the rpu block into one
    # field -> value map. Header/rpu key sets don't overlap.
    values = {**header, 'epoch_utc': epoch_utc, 'gps_datetime_utc': gps_datetime_utc}
    if rpu:
        values.update(rpu)

    def line(field):
        value = values.get(field)
        if isinstance(value, float) and float_fmt:
            print(f'{field}: {float_fmt.format(value)}')
        else:
            print(f'{field}: {value}')

    if csv_output:
        if first_file:
            print(','.join(ratchuts_report_csv_field_names))
        row = [values.get(f) for f in ratchuts_report_csv_field_names]
        print_list_csv(data=row, float_fmt=float_format)
    else:
        print('----- RATCHUTSREPORT:')
        for field in ratchuts_header_field_names:
            line(field)
        if rpu:
            line('gps_datetime_utc')
            for field in rpu_status_field_names:
                line(field)
        else:
            print('rpu: (none - header-only report)')
        print()
