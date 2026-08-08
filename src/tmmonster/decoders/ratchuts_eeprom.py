from datetime import datetime, timezone
import sys
import struct
from ..tm import TMmsg
from ..csv_util import print_list_csv

# Decoder for the RATCHUTS (PIB) EEPROM dump, sent as a TM with StateMess1
# "RATCHUTSEEPROM" (see StratoRatchuts::SendPIBEEPROM()).
#
# The payload is produced by TeensyEEPROM::Bufferize(), which copies the raw
# EEPROM bytes from start_addr to next_addr:
#   bytes 0-1 : CONFIG_VERSION (uint16, little-endian)
#   bytes 2+  : each registered EEPROMData<T>, raw little-endian, sizeof(T)
#               each, in RegisterAll() order, with no padding.
#
# Field order, types and CONFIG_VERSION come from PIBConfigs.h / PIBConfigs.cpp.
# To add a new config version, add an entry to pib_eeprom_fields keyed by its
# CONFIG_VERSION with the (name, struct_code) list in registration order.
#
# struct codes: f=float(4), I=uint32(4), H=uint16(2), B=uint8(1), ?=bool(1)

pib_eeprom_fields = {
    0x5C05: [
        ('config_version', 'H'),   # the version itself, bytes 0-1
        # profile triggers
        ('sza_minimum', 'f'),
        ('time_trigger', 'I'),
        ('sza_trigger', '?'),
        # profile sizing (revolutions)
        ('profile_size', 'f'),
        ('dock_amount', 'f'),
        ('dock_overshoot', 'f'),
        ('redock_out', 'f'),
        ('redock_in', 'f'),
        # profile speeds (rpm)
        ('deploy_velocity', 'f'),
        ('retract_velocity', 'f'),
        ('dock_velocity', 'f'),
        # RPU configuration
        ('rpu_bat_temp', 'f'),
        ('rpu_status_rate', 'H'),
        ('rpu_meas_duration', 'H'),
        ('rpu_meas_rate', 'H'),
        ('rpu_enable_TSEN', 'B'),
        ('rpu_enable_ROPC', 'B'),
        ('rpu_enable_RS41', 'B'),
        ('rpu_enable_TDLAS', 'B'),
        # profile timing (seconds)
        ('dwell_time', 'H'),
        ('preprofile_time', 'H'),
        ('puwarmup_time', 'H'),
        ('motion_timeout', 'H'),
        ('profile_period', 'H'),
        # autonomous configurations
        ('num_profiles', 'B'),
        ('num_redock', 'B'),
        # PU tracking
        ('pu_docked', '?'),
        # MCB TM mode
        ('real_time_mcb', '?'),
        # LoRa settings
        ('lora_tx_tm', '?'),
        ('lora_tx_status', 'H'),
        ('profile_id', 'H'),
        ('ra_override', '?'),
        ('pu_auto_offload', '?'),
    ],
    0x5C06: [
        ('config_version', 'H'),   # the version itself, bytes 0-1
        # profile sizing (revolutions)
        ('profile_size', 'f'),
        ('dock_amount', 'f'),
        ('dock_overshoot', 'f'),
        ('redock_out', 'f'),
        ('redock_in', 'f'),
        # profile speeds (rpm)
        ('deploy_velocity', 'f'),
        ('retract_velocity', 'f'),
        ('dock_velocity', 'f'),
        # RPU configuration
        ('rpu_bat_temp', 'f'),
        ('rpu_status_rate', 'H'),
        ('rpu_meas_duration', 'H'),
        ('rpu_meas_rate', 'H'),
        ('rpu_enable_TSEN', 'B'),
        ('rpu_enable_ROPC', 'B'),
        ('rpu_enable_RS41', 'B'),
        ('rpu_enable_TDLAS', 'B'),
        # profile timing (seconds)
        ('dwell_time', 'H'),
        ('preprofile_time', 'H'),
        ('puwarmup_time', 'H'),
        ('motion_timeout', 'H'),
        ('num_redock', 'B'),
        # PU tracking
        ('pu_docked', '?'),
        # MCB TM mode
        ('real_time_mcb', '?'),
        # LoRa settings
        ('lora_tx_tm', '?'),
        ('lora_tx_status', 'H'),
        ('profile_id', 'H'),
        ('ra_override', '?'),
        ('pu_auto_offload', '?'),
    ],
    0x5C07: [
        ('config_version', 'H'),   # the version itself, bytes 0-1
        # profile sizing (revolutions)
        ('profile_size', 'f'),
        ('dock_amount', 'f'),
        ('dock_overshoot', 'f'),
        ('redock_out', 'f'),
        ('redock_in', 'f'),
        # profile speeds (rpm)
        ('deploy_velocity', 'f'),
        ('retract_velocity', 'f'),
        ('dock_velocity', 'f'),
        # RPU configuration
        ('rpu_bat_temp', 'f'),
        ('rpu_status_rate', 'H'),
        ('rpu_meas_duration', 'H'),
        ('rpu_meas_rate', 'H'),
        ('rpu_enable_TSEN', 'B'),
        ('rpu_enable_ROPC', 'B'),
        ('rpu_enable_RS41', 'B'),
        ('rpu_enable_TDLAS', 'B'),
        # profile timing (seconds)
        ('dwell_time', 'H'),
        ('preprofile_time', 'H'),
        ('puwarmup_time', 'H'),
        ('motion_timeout', 'H'),
        ('num_redock', 'B'),
        # PU tracking
        ('pu_docked', '?'),
        # MCB TM mode
        ('real_time_mcb', '?'),
        # LoRa settings
        ('lora_tx_tm', '?'),
        ('lora_tx_status', 'H'),
        ('profile_id', 'H'),
        ('ra_override', '?'),
        # pu_auto_offload removed in 0x5C07 (dead config -- never written,
        # StratoCore_RACHUTS docked profile now always offloads)
    ],
}

versions = list(pib_eeprom_fields.keys())


def decode_payload(
    filename: str,
    print_headers: bool,
    print_payload: bool,
    first_file: bool,
    csv_output: bool,
    float_format: str
) -> None:
    payload = TMmsg(filename).bindata

    config_version = struct.unpack('<H', payload[0:2])[0]
    if config_version not in versions:
        print(f'Unknown RATCHUTSEEPROM config version 0x{config_version:04X}')
        sys.exit(1)

    if not print_payload:
        return

    fields = pib_eeprom_fields[config_version]

    # Unpack the fields sequentially, little-endian, no padding.
    eeprom = {}
    offset = 0
    for name, code in fields:
        size = struct.calcsize(code)
        eeprom[name] = struct.unpack_from('<' + code, payload, offset)[0]
        offset += size

    if first_file and csv_output:
        print(','.join(eeprom.keys()))

    if csv_output:
        csv_values = [
            f'0x{value:04X}' if field == 'config_version' else value
            for field, value in eeprom.items()
        ]
        print_list_csv(data=csv_values, float_fmt=float_format)
    else:
        float_fmt = f'{{:{float_format}}}' if float_format else None
        print("----- RATCHUTSEEPROM:")
        print(f'config_version: 0x{config_version:04X}')
        for key, value in eeprom.items():
            if key == 'config_version':
                continue
            if isinstance(value, float) and float_fmt:
                print(f'{key}: {float_fmt.format(value)}')
            else:
                print(f'{key}: {value}')
        print()
