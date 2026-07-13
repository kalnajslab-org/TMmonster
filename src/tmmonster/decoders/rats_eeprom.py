from datetime import datetime, timezone
import sys
import struct
from ..tm import TMmsg
from ..rats.bit_defs import *
from ..rats.scaled_vars import *
from ..csv_util import print_list_csv

# The CONFIG_VERSION is included in the data; the BASE_ADDRESS is not.
# From RATSConfigs.h (version 0x000C):
    # static const uint16_t CONFIG_VERSION = 0x000C;
    # static const uint16_t BASE_ADDRESS = 0x0000;

    # ------------------ Configurations ------------------
    # EEPROMData<uint16_t> decimate_factor;
    # EEPROMData<float> ecu_tempC;
    # EEPROMData<float> deploy_velocity;   # revs/min
    # EEPROMData<float> retract_velocity;  # revs/min
    # EEPROMData<uint16_t> motion_timeout;
    # EEPROMData<bool> real_time_mcb;
    # EEPROMData<uint8_t> paired_ecu;     # ECU ID to pair with

rats_eeprom_field_names = {
    0x000C: [
        'config_version',
        'decimate_factor',
        'ecu_tempC',
        'deploy_velocity',
        'retract_velocity',
        'motion_timeout',
        'real_time_mcb',
        'paired_ecu'
    ]
}

versions = [0x000C]

def decode_payload(
    filename: str,
    print_headers: bool,
    print_payload: bool,
    first_file: bool,
    csv_output: bool,
    float_format: str
) -> None:
    payload = TMmsg(filename).bindata

    eeprom = {}
    eeprom['config_version'] = struct.unpack('<H', payload[0:2])[0]

    if eeprom['config_version'] not in versions:
        print(f'Unknown RATSEEPROM header version {eeprom["config_version"]}')
        sys.exit(1)

    if not print_payload:
        return  

    eeprom['decimate_factor'] = struct.unpack('<H', payload[2:4])[0]
    eeprom['ecu_tempC'] = struct.unpack('<f', payload[4:8])[0]
    eeprom['deploy_velocity'] = struct.unpack('<f', payload[8:12])[0]
    eeprom['retract_velocity'] = struct.unpack('<f', payload[12:16])[0]
    eeprom['motion_timeout'] = struct.unpack('<H',payload[16:18])[0]
    eeprom['real_time_mcb'] = bool(payload[18])
    eeprom['paired_ecu'] = payload[19]

    if first_file and csv_output:
        csv_col_names = ','.join(name for name in eeprom.keys())
        print(csv_col_names)

    if csv_output:
        csv_values = [eeprom[field] for field in eeprom.keys()]
        print_list_csv(data=csv_values, float_fmt=float_format)
    else:
        float_fmt = f'{{:{float_format}}}' if float_format else None
        print("----- RATSEEPROM:")
        for key, value in eeprom.items():
            if isinstance(value, float) and float_fmt:
                print(f'{key}: {float_fmt.format(value)}')
            else:
                print(f'{key}: {value}')
        print()
