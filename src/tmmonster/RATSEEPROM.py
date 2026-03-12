import sys
import struct
from .TMmsg import TMmsg
from .TMCSV import print_list_csv

# The CONFIG_VERSION is included in the data; the BASE_ADDRESS is not.
# From RATSConfigs.h (version 0x000C):
    # static const uint16_t CONFIG_VERSION = 0x000C;
    # static const uint16_t BASE_ADDRESS = 0x0000;

    # ------------------ Configurations ------------------
    # EEPROMData<uint16_t> data_proc_method;
    # EEPROMData<float> ecu_tempC;
    # EEPROMData<float> deploy_velocity;   # revs/min
    # EEPROMData<float> retract_velocity;  # revs/min
    # EEPROMData<uint16_t> motion_timeout;
    # EEPROMData<bool> real_time_mcb;
    # EEPROMData<uint8_t> paired_ecu;     # ECU ID to pair with

rats_eeprom_field_names = {
    0x000C: [
        'config_version',
        'data_proc_method',
        'ecu_tempC',
        'deploy_velocity',
        'retract_velocity',
        'motion_timeout',
        'real_time_mcb',
        'paired_ecu'
    ]
}

versions = [0x000C]

class RATSEEPROMmsg(TMmsg):
    def __init__(self, msg_filename: str):
        super().__init__(msg_filename)
        self.eeprom = self._unpack()

    def _unpack(self) -> dict:
        p = self.bindata
        return {
            'config_version':  struct.unpack('<H', p[0:2])[0],
            'data_proc_method': struct.unpack('<H', p[2:4])[0],
            'ecu_tempC':        struct.unpack('<f', p[4:8])[0],
            'deploy_velocity':  struct.unpack('<f', p[8:12])[0],
            'retract_velocity': struct.unpack('<f', p[12:16])[0],
            'motion_timeout':   struct.unpack('<H', p[16:18])[0],
            'real_time_mcb':    bool(p[18]),
            'paired_ecu':       p[19],
        }

def decode_payload(
    filename: str,
    print_headers: bool,
    print_payload: bool,
    first_file: bool,
    csv_output: bool,
    float_format: str
) -> None:
    msg = RATSEEPROMmsg(filename)
    eeprom = msg.eeprom

    if eeprom['config_version'] not in versions:
        print(f'Unknown RATSEEPROM header version {eeprom["config_version"]}')
        sys.exit(1)

    if not print_payload:
        return

    if first_file and csv_output:
        print(','.join(eeprom.keys()))

    if csv_output:
        print_list_csv(data=list(eeprom.values()), float_fmt=float_format)
    else:
        float_fmt = f'{{:{float_format}}}' if float_format else None
        for key, value in eeprom.items():
            if isinstance(value, float) and float_fmt:
                print(f'{key}: {float_fmt.format(value)}')
            else:
                print(f'{key}: {value}')
        print()
