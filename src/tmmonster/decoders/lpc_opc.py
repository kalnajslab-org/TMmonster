import struct
from datetime import datetime, timezone
from ..tm import TMmsg
from ..csv_util import print_list_csv

def decode_payload(
    filename: str,
    print_headers: bool,
    print_payload: bool,
    first_file: bool,
    csv_output: bool,
    float_format: str
) -> None:
    opc_msg = LPCmsg(filename)
    if print_payload:
        if csv_output:
            if first_file:
                print(','.join(opc_msg.opcParamNames()))
                print(','.join(opc_msg.opcParamUnits()))
            for r in opc_msg.records:
                print_list_csv([r[v] for v in opc_msg.opcParamNames()], float_format)
        else:
            float_fmt = f'{{:{float_format}}}' if float_format else None
            for i, r in enumerate(opc_msg.records):
                print(f'----- OPC record {i}:')
                for k, v in r.items():
                    val = float_fmt.format(v) if isinstance(v, float) and float_fmt else v
                    print(f'  {k}: {val}')
                print()

# HG bins cover the smaller particle sizes (high gain detector)
# LG bins cover the larger particle sizes (low gain detector)
# Each number is the left edge of the bin in nm.
_HG_DIAMS = [275, 300, 325, 350, 375, 400, 450, 500, 550, 600, 650, 700, 750, 800, 900, 1000]
_LG_DIAMS = [1200, 1400, 1600, 1800, 2000, 2500, 3000, 3500, 4000, 6000, 8000, 10000, 13000, 16000, 24000, 24000]

_HK_NAMES = ['epoch', 'epoch_utc', 'lat_deg', 'lon_deg', 'alt_m', 'pump1_I_mA', 'pump2_I_mA', 'pha_I_mA',
             'pha_12V_V', 'pha_3V3_V', 'cpu_V_V', 'input_V_V',
             'flow_SLPM', 'pump1_PWM', 'pump2_PWM', 'pump1_T_degC',
             'pump2_T_degC', 'laser_T_degC', 'pcb_T_degC', 'inlet_T_degC']

_HK_UNITS = ['[epoch]', '[iso8601]', '[deg]', '[deg]', '[m]', '[mA]', '[mA]', '[mA]', '[V]', '[V]', '[V]', '[V]',
             '[SLPM]', '[#]', '[#]', '[C]', '[C]', '[C]', '[C]', '[C]']


def _bin_field_names(prefix, diams):
    seen = {}
    names = []
    for d in diams:
        key = f'{prefix}_{d}'
        if key in seen:
            seen[key] += 1
            names.append(f'{key}_{seen[key]}')
        else:
            seen[key] = 0
            names.append(key)
    return names

class LPCmsg(TMmsg):
    def __init__(self, msg_filename: str):
        super().__init__(msg_filename)

        self.sn = 'Unknown'
        self.lat = ''
        self.lon = ''
        self.alt = ''

        tm_xml = self.parse_TM_xml()

        # StateMess2 carries the lat,lon,alt string for OPC messages (it's
        # what distinguishes LPCOPC from LPCRS41 in get_report_type: RS41
        # messages have StateMess2 == "RS41", OPC messages have position
        # there instead). StateMess3, when present, just repeats it, but
        # isn't always sent -- so read from StateMess2.
        if 'StateMess2' in tm_xml['TM']:
            tokens = tm_xml['TM']['StateMess2'].split(',')
            if len(tokens) == 3:
                self.lat = tokens[0]
                self.lon = tokens[1]
                self.alt = tokens[2]

        self.records = self._unpackBinary()

    def opcParamNames(self) -> list:
        return (_HK_NAMES +
                _bin_field_names('hg', _HG_DIAMS) +
                _bin_field_names('lg', _LG_DIAMS))

    def opcParamUnits(self) -> list:
        return (_HK_UNITS +
                ['[diam >nm]'] * len(_HG_DIAMS) +
                ['[diam >nm]'] * len(_LG_DIAMS))

    def _unpackBinary(self) -> list:
        num_records = int(len(self.bindata) / 96) - 2
        hg_names = _bin_field_names('hg', _HG_DIAMS)
        lg_names = _bin_field_names('lg', _LG_DIAMS)
        records = []
        for y in range(num_records):
            r = {}
            indx = 36 + (y + 1) * 96

            hk_raw = []
            hg_vals = []
            lg_vals = []
            for x in range(16):
                hg_vals.append(struct.unpack_from('>H', self.bindata, indx + x * 2)[0])
                lg_vals.append(struct.unpack_from('>H', self.bindata, indx + x * 2 + 32)[0])
                hk_raw.append(struct.unpack_from('>H', self.bindata, indx + x * 2 + 64)[0])

            # HK fields first (insertion order matches opcParamNames)
            r['epoch'] = hk_raw[0] + self.unix_end_time
            r['epoch_utc'] = datetime.fromtimestamp(r['epoch'], tz=timezone.utc).isoformat().replace('+00:00', 'Z')
            # lat/lon/alt are the position at the start of the message
            # (from StateMess3), not per-record GPS; only the first record
            # of the message carries it.
            r['lat_deg'] = self.lat if y == 0 else ''
            r['lon_deg'] = self.lon if y == 0 else ''
            r['alt_m'] = self.alt if y == 0 else ''
            r['pump1_I_mA'] = float(hk_raw[1])
            r['pump2_I_mA'] = float(hk_raw[2])
            r['pha_I_mA'] = float(hk_raw[3])
            r['pha_12V_V'] = hk_raw[4] / 1000.0
            r['pha_3V3_V'] = hk_raw[5] / 1000.0
            r['cpu_V_V'] = hk_raw[6] / 1000.0
            r['input_V_V'] = hk_raw[7] / 1000.0
            r['flow_SLPM'] = hk_raw[8] / 1000.0
            r['pump1_PWM'] = float(hk_raw[9])
            r['pump2_PWM'] = float(hk_raw[10])
            r['pump1_T_degC'] = hk_raw[11] / 100.0 - 273.15
            r['pump2_T_degC'] = hk_raw[12] / 100.0 - 273.15
            r['laser_T_degC'] = hk_raw[13] / 100.0 - 273.15
            r['pcb_T_degC'] = hk_raw[14] / 100.0 - 273.15
            r['inlet_T_degC'] = hk_raw[15] / 100.0 - 273.15

            for name, val in zip(hg_names, hg_vals):
                r[name] = float(val)
            for name, val in zip(lg_names, lg_vals):
                r[name] = float(val)

            records.append(r)
        return records
