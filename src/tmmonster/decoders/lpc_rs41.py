from typing import Optional
import struct
import csv
import io
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
                # Print header lines (metadata + column names)
                    print(",".join(rs41_tmmsg.csvTitleFields()))
                    print(",".join(rs41_tmmsg.rs41ParamNames()))
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

class RS41msg(TMmsg):
    # The binary payload for the RS41 contains a couple of
    # metadata fields, followed by multiple data records.
    # The payload is coded as follows:
    # uint32_t start time
    # uint16_t n_samples
    # data records:
    # struct RS41Sample_t {
    #    uint8_t valid;
    #    uint32_t frame;
    #    uint16_t tdry; (tdry+100)*100
    #    uint16_t humidity; (humdity*100)
    #    uint16_t pres; (pres*100)
    #    uint16_t error;
    #};
    def __init__(self, msg_filename:str):
        '''
        Initialize the object with the provided binary data.

        Args:
            msg_filename: The message file name.

        Returns:
            None
        '''
        super().__init__(msg_filename)
        self.records = self.allRS41samples()

    def csvTitleFields(self) -> list:
        '''
        Create a CSV header for the output.

        Returns:
            list: A list representing the CSV header.
        '''
        title = ['Instrument:', 'RS41', 'Measurement End Time:', self.formatted_time, 
                   'NCAR RS41 sensor on Strateole 2 Super Pressure Balloons']
        return title

    def rs41ParamNames(self) -> list:
        return ['valid', 'unix_time', 'air_temp_degC', 'humdity_percent',
                'humidity_sensor_temp_degC', 'pres_mb', 'module_error',
                'rs41_rh_percent', 'wv_mixing_ratio_ppmv']

    def decodeRS41sample(self, record)->dict:
        '''
        Decode a binary sample and convert it to real-world values.

        Args:
            record: The binary sample to decode.

        Returns:
            dict: Decoded real-world values of the binary sample.
        '''
        r = {}
        r['valid'] = bool(struct.unpack_from('B', record, 0)[0])
        r['secs_from_start'] = struct.unpack_from('>l', record, 1)[0]
        # print('decodeRS41',self.unix_end_time,r['unix_time'])
        r['air_temp_degC'] = struct.unpack_from('>H', record, 5)[0]/100.0-100.0
        r['humdity_percent'] = struct.unpack_from('>H', record, 7)[0]/100.0
        r['humidity_sensor_temp_degC'] = struct.unpack_from('>H', record, 9)[0]/100.0-100.0
        r['pres_mb'] = struct.unpack_from('>H', record, 11)[0]/50.0
        r['module_error'] = struct.unpack_from('>H', record, 13)[0]
        r['rs41_rh_percent'],r['wv_mixing_ratio_ppmv']=RS41_RH_wvmr(r['air_temp_degC'],r['pres_mb'],r['humdity_percent'],r['humidity_sensor_temp_degC'])
        #print(r)
        return r
    
    def allRS41samples(self)->list:
        '''
        Go through all data samples and convert them to real-world values.

        Returns:
            list: List of dictionaries containing decoded real-world values for each data sample.
        '''
        record_len = 1 + 4 + 2 + 2 + 2 + 2 + 2
        records = []
        for i in range(6, len(self.bindata)-6, record_len):
            record = self.bindata[i:i+record_len]
            records.append(self.decodeRS41sample(record))

        # Compute the unix time for each sample
        start_time = self.unix_end_time - (records[-1]['secs_from_start'] - records[0]['secs_from_start'] + 1)
        for i in range(len(records)):
            records[i]['unix_time'] =  records[i]['secs_from_start'] + start_time

        return records

