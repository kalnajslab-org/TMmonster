from typing import Optional
import struct
import csv
import io
from datetime import datetime, timezone
import numpy as np
import glob as glob

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
    rs41_tmmsg = RS41msg(filename)
    if print_payload:
        if csv_output:
            if first_file:
                print(",".join(rs41_tmmsg.rs41ParamNames()))
                print(",".join(rs41_tmmsg.rs41ParamUnits()))
            for r in rs41_tmmsg.records:
                print_list_csv([r[v] for v in rs41_tmmsg.rs41ParamNames()], float_format)
        else:
            float_fmt = f'{{:{float_format}}}' if float_format else None
            for i, r in enumerate(rs41_tmmsg.records):
                print(f'----- RS41 record {i}:')
                for k, v in r.items():
                    val = float_fmt.format(v) if isinstance(v, float) and float_fmt else v
                    print(f'  {k}: {val}')
                print()

def RS41_RH_wvmr(TC_ambient,hPa_ambient,rh_reported,TC_humSensor):
    '''
    Parameters: ambient:tempC,prshPa, RH_reported, tempC_of humSensor
    Returns: ambient RH and ambient water vapor mixing ratio ppmv
    '''
    eswhPa_humSensor_temp=Hardy_1998(TC_humSensor)
    eswhPa_ambient_temp=Hardy_1998(TC_ambient)
    ew_hPa=eswhPa_humSensor_temp*rh_reported/100.
    RH_ambient = ew_hPa/eswhPa_ambient_temp*100 if eswhPa_ambient_temp != 0 else float('nan')
    WV_ppmv=WV_mixing_ratio(ew_hPa,hPa_ambient)
    return [RH_ambient,WV_ppmv]

def WV_mixing_ratio(ew_hPa,prshPa):
    '''
    Parameters: vapor pressure of water, ambient pressure 
    calculates water vapor mixing ratio (ppm) in both mass (ppmm) and volume(ppmv)
    Returns: WV_ppmv 
    '''
    molecw_air=28.97
    molecw_h2o=18.0
    epsilon=molecw_h2o/molecw_air
    denom = prshPa - ew_hPa
    if denom == 0:
        return float('nan')
    WV_ppmm=epsilon*ew_hPa/denom*1e6
    WV_ppmv=ew_hPa/denom*1e6
    return WV_ppmv

def Hardy_1998(TC):
   '''
   Returns saturation vapor pressure in hPa esw_hPa at TC from Hardy (1998)
   Parameters Temp C
   This is the formulation used by Vaisala the maker of the RS41
   '''
   HC=[-2.8365744e3,-6.028076559e3,1.954263612e1,-2.737830188e-2,1.6261698e-5,7.0229056e-10,-1.8680009e-13]
   TK=TC+273.15
   i=0
   lesw=0
   for c in HC:
       lesw=lesw+c*TK**(i-2)
       i=i+1
   lesw=lesw+2.7150305*np.log(TK)
   esw_hPa=np.exp(lesw)/100
   return esw_hPa

def _decodeRS41sample_common(record) -> dict:
    r = {}
    r['valid'] = bool(struct.unpack_from('B', record, 0)[0])
    r['secs_from_start'] = struct.unpack_from('>l', record, 1)[0]
    r['air_temp_degC'] = struct.unpack_from('>H', record, 5)[0]/100.0-100.0
    r['humdity_percent'] = struct.unpack_from('>H', record, 7)[0]/100.0
    return r


def _decodeRS41sample_v1(record) -> dict:
    '''
    13-byte record (pre-tsensor firmware, e.g. archived pre-2024-06 TMs):
    valid(1) + frame(4) + tdry(2) + humidity(2) + pres(2) + error(2).
    No humidity-sensor-temperature reading, so RH/mixing-ratio can't be derived.
    '''
    r = _decodeRS41sample_common(record)
    r['humidity_sensor_temp_degC'] = float('nan')
    r['pres_mb'] = struct.unpack_from('>H', record, 9)[0]/50.0
    r['module_error'] = struct.unpack_from('>H', record, 11)[0]
    r['rs41_rh_percent'] = float('nan')
    r['wv_mixing_ratio_ppmv'] = float('nan')
    return r


def _decodeRS41sample_v2(record) -> dict:
    '''
    15-byte record (current firmware, StratoLPC.h rs41TmSample_t):
    valid(1) + frame(4) + tdry(2) + humidity(2) + tsensor(2) + pres(2) + error(2).
    '''
    r = _decodeRS41sample_common(record)
    r['humidity_sensor_temp_degC'] = struct.unpack_from('>H', record, 9)[0]/100.0-100.0
    r['pres_mb'] = struct.unpack_from('>H', record, 11)[0]/50.0
    r['module_error'] = struct.unpack_from('>H', record, 13)[0]
    r['rs41_rh_percent'],r['wv_mixing_ratio_ppmv']=RS41_RH_wvmr(r['air_temp_degC'],r['pres_mb'],r['humdity_percent'],r['humidity_sensor_temp_degC'])
    return r


# Record length is the only version signal on the wire (no explicit format
# tag) — keyed by the byte length of one record, derived per-message from
# the header's n_samples field. Add new firmware formats here by byte length.
RS41_FORMATS = {
    13: _decodeRS41sample_v1,
    15: _decodeRS41sample_v2,
}


class RS41msg(TMmsg):
    # The binary payload for the RS41 contains a couple of
    # metadata fields, followed by multiple data records.
    # The payload is coded as follows:
    # uint32_t start time
    # uint16_t n_samples
    # data records: see RS41_FORMATS for the per-version record layout.
    def __init__(self, msg_filename:str):
        '''
        Initialize the object with the provided binary data.

        Args:
            msg_filename: The message file name.

        Returns:
            None
        '''
        super().__init__(msg_filename)

        self.lat = ''
        self.lon = ''
        self.alt = ''
        tm_xml = self.parse_TM_xml()
        if 'StateMess3' in tm_xml['TM']:
            tokens = tm_xml['TM']['StateMess3'].split(',')
            if len(tokens) == 3:
                self.lat, self.lon, self.alt = tokens

        self.records = self.allRS41samples()

    def rs41ParamNames(self) -> list:
        return ['valid', 'epoch', 'epoch_utc', 'lat_deg', 'lon_deg', 'alt_m', 'air_temp_degC', 'humdity_percent',
                'humidity_sensor_temp_degC', 'pres_mb', 'module_error',
                'rs41_rh_percent', 'wv_mixing_ratio_ppmv']

    def rs41ParamUnits(self) -> list:
        return ['[bool]', '[epoch]', '[iso8601]', '[deg]', '[deg]', '[m]', '[C]', '[%]',
                '[C]', '[mb]', '[#]',
                '[%]', '[ppmv]']

    def decodeRS41sample(self, record, record_len)->dict:
        '''
        Decode a binary sample and convert it to real-world values.

        Args:
            record: The binary sample to decode.
            record_len: Byte length of the record, used to select the
                firmware format's decoder (see RS41_FORMATS).

        Returns:
            dict: Decoded real-world values of the binary sample.
        '''
        decoder = RS41_FORMATS.get(record_len)
        if decoder is None:
            raise ValueError(
                f"Unrecognized RS41 record length {record_len} bytes; "
                f"known formats: {sorted(RS41_FORMATS)}"
            )
        return decoder(record)

    def allRS41samples(self)->list:
        '''
        Go through all data samples and convert them to real-world values.

        Returns:
            list: List of dictionaries containing decoded real-world values for each data sample.
        '''
        HEADER_LEN = 6
        n_samples = struct.unpack_from('>H', self.bindata, 4)[0]
        record_len = (len(self.bindata) - HEADER_LEN) // n_samples

        records = []
        for i in range(n_samples):
            offset = HEADER_LEN + i * record_len
            record = self.bindata[offset:offset+record_len]
            records.append(self.decodeRS41sample(record, record_len))

        # Compute the unix time for each sample
        start_time = self.unix_end_time - (records[-1]['secs_from_start'] - records[0]['secs_from_start'] + 1)
        for i in range(len(records)):
            records[i]['epoch'] = records[i]['secs_from_start'] + start_time
            records[i]['epoch_utc'] = datetime.fromtimestamp(records[i]['epoch'], tz=timezone.utc).isoformat().replace('+00:00', 'Z')
            # lat/lon/alt are the position at the start of the message
            # (from StateMess3), not per-record GPS; only the first record
            # of the message carries it.
            records[i]['lat_deg'] = self.lat if i == 0 else ''
            records[i]['lon_deg'] = self.lon if i == 0 else ''
            records[i]['alt_m'] = self.alt if i == 0 else ''

        return records

