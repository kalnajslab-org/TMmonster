import sys
import struct
from .TMmsg import TMmsg
from .TMCSV import print_list_csv

# Sentinel values used in ConfigManagerMCB to mark a limit as "not in use"
_FLT_MAX = struct.unpack('<f', bytes([0xFF, 0xFF, 0x7F, 0x7F]))[0]
_FLT_MIN = struct.unpack('<f', bytes([0x00, 0x00, 0x80, 0x00]))[0]

# From ConfigManagerMCB.h / ConfigManagerMCB.cpp (CONFIG_VERSION 0x5C01):
#
#   static const uint16_t CONFIG_VERSION = 0x5C01;
#   static const uint16_t BASE_ADDRESS   = 0x0000;
#
#   EEPROMData<uint32_t>      boot_count
#   EEPROMData<float>         deploy_velocity
#   EEPROMData<float>         deploy_acceleration
#   EEPROMData<float>         retract_velocity
#   EEPROMData<float>         retract_acceleration
#   EEPROMData<float>         dock_velocity
#   EEPROMData<float>         dock_acceleration
#   EEPROMData<Limit_Config_t> mtr1_temp_lim      {float hi, float lo}
#   EEPROMData<Limit_Config_t> mtr2_temp_lim
#   EEPROMData<Limit_Config_t> mc1_temp_lim
#   EEPROMData<Limit_Config_t> mc2_temp_lim
#   EEPROMData<Limit_Config_t> dcdc_temp_lim
#   EEPROMData<Limit_Config_t> spare_therm_lim
#   EEPROMData<Limit_Config_t> vmon_3v3_lim
#   EEPROMData<Limit_Config_t> vmon_15v_lim
#   EEPROMData<Limit_Config_t> vmon_20v_lim
#   EEPROMData<Limit_Config_t> vmon_spool_lim
#   EEPROMData<Limit_Config_t> imon_brake_lim
#   EEPROMData<Limit_Config_t> imon_mc_lim
#   EEPROMData<Limit_Config_t> imon_mtr1_lim
#   EEPROMData<Limit_Config_t> imon_mtr2_lim
#   EEPROMData<Limit_Config_t> reel_torque_lim
#   EEPROMData<Limit_Config_t> lw_torque_lim
#   EEPROMData<uint8_t>        tmslow_num_samples
#   EEPROMData<uint8_t>        tmfast_num_samples
#   EEPROMData<bool>           limits_enabled
#
# TeensyEEPROM::Bufferize() reads from BASE_ADDRESS (includes the version uint16_t),
# then all registered fields sequentially. All values are little-endian (Teensy ARM).

versions = [0x5C01]

# (field_name, struct_fmt)  — in order as stored in EEPROM after the 2-byte version
_fields = [
    ('boot_count',           '<I'),   # uint32_t
    ('deploy_velocity',      '<f'),   # float
    ('deploy_acceleration',  '<f'),
    ('retract_velocity',     '<f'),
    ('retract_acceleration', '<f'),
    ('dock_velocity',        '<f'),
    ('dock_acceleration',    '<f'),
    ('mtr1_temp_lim_hi',     '<f'),   # Limit_Config_t { float hi; float lo; }
    ('mtr1_temp_lim_lo',     '<f'),
    ('mtr2_temp_lim_hi',     '<f'),
    ('mtr2_temp_lim_lo',     '<f'),
    ('mc1_temp_lim_hi',      '<f'),
    ('mc1_temp_lim_lo',      '<f'),
    ('mc2_temp_lim_hi',      '<f'),
    ('mc2_temp_lim_lo',      '<f'),
    ('dcdc_temp_lim_hi',     '<f'),
    ('dcdc_temp_lim_lo',     '<f'),
    ('spare_therm_lim_hi',   '<f'),
    ('spare_therm_lim_lo',   '<f'),
    ('vmon_3v3_lim_hi',      '<f'),
    ('vmon_3v3_lim_lo',      '<f'),
    ('vmon_15v_lim_hi',      '<f'),
    ('vmon_15v_lim_lo',      '<f'),
    ('vmon_20v_lim_hi',      '<f'),
    ('vmon_20v_lim_lo',      '<f'),
    ('vmon_spool_lim_hi',    '<f'),
    ('vmon_spool_lim_lo',    '<f'),
    ('imon_brake_lim_hi',    '<f'),
    ('imon_brake_lim_lo',    '<f'),
    ('imon_mc_lim_hi',       '<f'),
    ('imon_mc_lim_lo',       '<f'),
    ('imon_mtr1_lim_hi',     '<f'),
    ('imon_mtr1_lim_lo',     '<f'),
    ('imon_mtr2_lim_hi',     '<f'),
    ('imon_mtr2_lim_lo',     '<f'),
    ('reel_torque_lim_hi',   '<f'),
    ('reel_torque_lim_lo',   '<f'),
    ('lw_torque_lim_hi',     '<f'),
    ('lw_torque_lim_lo',     '<f'),
    ('tmslow_num_samples',   '<B'),   # uint8_t
    ('tmfast_num_samples',   '<B'),
    ('limits_enabled',       '<?'),   # bool
]


class MCBEEPROMmsg(TMmsg):
    def __init__(self, msg_filename: str):
        super().__init__(msg_filename)
        self.eeprom = self._unpack()

    def _unpack(self) -> dict:
        p = self.bindata
        eeprom = {'config_version': struct.unpack_from('<H', p, 0)[0]}
        offset = 2  # skip the uint16_t version
        for name, fmt in _fields:
            eeprom[name] = struct.unpack_from(fmt, p, offset)[0]
            offset += struct.calcsize(fmt)
        return eeprom


def decode_payload(
    filename: str,
    print_headers: bool,
    print_payload: bool,
    first_file: bool,
    csv_output: bool,
    float_format: str
) -> None:
    msg = MCBEEPROMmsg(filename)
    eeprom = msg.eeprom

    if eeprom['config_version'] not in versions:
        print(f'Unknown MCBEEPROM config version 0x{eeprom["config_version"]:04X}')
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
            if key == 'config_version':
                print(f'{key}: 0x{value:04X}')
            elif isinstance(value, float) and value == _FLT_MAX:
                print(f'{key}: {value}  (disabled: FLT_MAX)')
            elif isinstance(value, float) and value == _FLT_MIN:
                print(f'{key}: {value}  (disabled: FLT_MIN)')
            elif isinstance(value, float) and float_fmt:
                print(f'{key}: {float_fmt.format(value)}')
            else:
                print(f'{key}: {value}')
        print()
