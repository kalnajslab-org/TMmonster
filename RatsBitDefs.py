# Definitions for RATSReport and ECUReport bitfields and field names

# RATSReport header bitfield formats by version
# The header is defined in StratoCore_RATS/src/StratoRats.h as StratoRats::RATSReportHeader_t.

rats_bits = {
    0: (
    '>'    # little-endian
    'u4'   # The version of the RATS report header.
    'u4'   # header_size_bytes (4 bits)
    'u16'  # num_ecu_records (16 bits)
    'u16'  # ecu_record_size_bytes (16 bits)
    'u1'   # ecu_pwr_on (1 bit)
    'u13'  # v56 (13 bits)
   ),
   1: (
    '>'    # little-endian
    'u4'   # The version of the RATS report header.
    'u8'   # header_size_bytes (4 bits)
    'u10'  # num_ecu_records (10 bits)
    'u9'   # ecu_record_size_bytes (9 bits)
    'u1'   # ecu_pwr_on (1 bit)
    'u13'  # v56 (13 bits)
    'u11'  # cpu_temp (11 bits)
    'u10'  # lora_rssi (10 bits)
    'u10'  # lora_snr (10 bits)
   ),
   2: (
    '>'    # little-endian
    'u4'   # The version of the RATS report header.
    'u8'   # header_size_bytes (4 bits)
    'u10'  # num_ecu_records (10 bits)
    'u9'   # ecu_record_size_bytes (9 bits)
    'u1'   # ecu_pwr_on (1 bit)
    'u13'  # v56 (13 bits)
    'u11'  # cpu_temp (11 bits)
    'u10'  # lora_rssi (10 bits)
    'u10'  # lora_snr (10 bits)
    'u11'  # inst_imon (11 bits)
   ),
   3: (
    '>'    # little-endian
    'u4'   # The version of the RATS report header.
    'u16'  # rats_id (16 bits)
    'u8'   # paired_ecu (8 bits)
    'u8'   # header_size_bytes (8 bits)
    'u10'  # num_ecu_records (10 bits)
    'u9'   # ecu_record_size_bytes (9 bits)
    'u1'   # ecu_pwr_on (1 bit)
    'u13'  # v56 (13 bits)
    'u11'  # cpu_temp (11 bits)
    'u10'  # lora_rssi (10 bits)
    'u10'  # lora_snr (10 bits)
    'u11'  # inst_imon (11 bits)
    ),
   4: (
    '>'    # little-endian
    'u4'   # The version of the RATS report header.
    'u16'  # rats_id (16 bits)
    'u32'  # epoch_time (32 bits)
    'u8'   # paired_ecu (8 bits)
    'u8'   # header_size_bytes (8 bits)
    'u10'  # num_ecu_records (10 bits)
    'u9'   # ecu_record_size_bytes (9 bits)
    'u1'   # ecu_pwr_on (1 bit)
    'u13'  # v56 (13 bits)
    'u11'  # cpu_temp (11 bits)
    'u10'  # lora_rssi (10 bits)
    'u10'  # lora_snr (10 bits)
    'u11'  # inst_imon (11 bits)
    )
}

rats_field_names = {
    0:[
    'rats_report_rev',
    'header_size_bytes', 
    'num_ecu_records', 
    'ecu_record_size_bytes', 
    'ecu_pwr_on', 
    'v56'
    ],
    1:[
    'rats_report_rev',
    'header_size_bytes',
    'num_ecu_records',
    'ecu_record_size_bytes',
    'ecu_pwr_on',
    'v56',
    'cpu_temp',
    'lora_rssi',
    'lora_snr'
    ],
    2:[
    'rats_report_rev',
    'header_size_bytes',
    'num_ecu_records',
    'ecu_record_size_bytes',
    'ecu_pwr_on',
    'v56',
    'cpu_temp',
    'lora_rssi',
    'lora_snr',
    'inst_imon'
    ],
    3:[ 
    'rats_report_rev',
    'rats_id',
    'paired_ecu',
    'header_size_bytes',
    'num_ecu_records',
    'ecu_record_size_bytes',
    'ecu_pwr_on',
    'v56',
    'cpu_temp',
    'lora_rssi',
    'lora_snr',
    'inst_imon',
    ],
    4:[
    'rats_report_rev',
    'rats_id',
    'epoch_time',
    'paired_ecu',
    'header_size_bytes',
    'num_ecu_records',
    'ecu_record_size_bytes',
    'ecu_pwr_on',
    'v56',
    'cpu_temp',
    'lora_rssi',
    'lora_snr',
    'inst_imon',
    ]
}

ecu_bits = {
    1: (
        '>'    # little-endian
        'u4'   # rev (4 bits)
        'u1'   # heat_on (1 bit)
        'u9'   # v5 (9 bits)
        'u11'  # v12 (11 bits)
        'u13'  # v56 (13 bits)
        'u11'  # board_t (11 bits)
        'u8'   # switch_mA (8 bits)
        'u1'   # gps_valid (1 bit)
        's32'  # gps_lat (32 bits)
        's32'  # gps_lon (32 bits)
        'u16'  # gps_alt (16 bits)
        'u5'   # gps_sats (5 bits)
        'u17'  # gps_date (17 bits)
        'u25'  # gps_time (25 bits)
        'u8'   # gps_age_secs (8 bits)
        'u1'   # rs41_valid (1 bit)
        'u14'  # rs41_airt (14 bits)
        'u10'  # rs41_hum (10 bits)
        'u8'   # rs41_hst (8 bits)
        'u17'  # rs41_pres (17 bits)
        'u1'   # rs41_pcb_h (1 bit)
        'u12'  # tsen_airt (12 bits)
        'u24'  # tsen_ptemp (24 bits)
        'u24'  # tsen_pres (24 bits)
    ),
    2: (
        '>'    # little-endian
        'u4'   # rev (4 bits)
        'u1'   # heat_on (1 bit)
        'u9'   # v5 (9 bits)
        'u11'  # v12 (11 bits)
        'u13'  # v56 (13 bits)
        'u11'  # board_t (11 bits)
        'u8'   # temp_setpoint (8 bits)
        'u8'   # switch_mA (8 bits)
        'u1'   # gps_valid (1 bit)
        's32'  # gps_lat (32 bits)
        's32'  # gps_lon (32 bits)
        'u16'  # gps_alt (16 bits)
        'u5'   # gps_sats (5 bits)
        'u17'  # gps_date (17 bits)
        'u25'  # gps_time (25 bits)
        'u8'   # gps_age_secs (8 bits)
        'u1'   # rs41_valid (1 bit)
        'u14'  # rs41_airt (14 bits)
        'u10'  # rs41_hum (10 bits)
        'u8'   # rs41_hst (8 bits)
        'u17'  # rs41_pres (17 bits)
        'u1'   # rs41_pcb_h (1 bit)
        'u12'  # tsen_airt (12 bits)
        'u24'  # tsen_ptemp (24 bits)
        'u24'  # tsen_pres (24 bits)
    ),
    3: (
        '>'    # little-endian
        'u4'   # rev (4 bits)
        'u1'   # heat_on (1 bit)
        'u9'   # v5 (9 bits)
        'u11'  # v12 (11 bits)
        'u13'  # v56 (13 bits)
        'u11'  # board_t (11 bits)
        'u8'   # temp_setpoint (8 bits)
        'u8'   # switch_mA (8 bits)
        'u1'   # gps_valid (1 bit)
        's32'  # gps_lat (32 bits)
        's32'  # gps_lon (32 bits)
        'u16'  # gps_alt (16 bits)
        'u5'   # gps_sats (5 bits)
        'u17'  # gps_date (17 bits)
        'u25'  # gps_time (25 bits)
        'u8'   # gps_age_secs (8 bits)
        'u1'   # rs41_valid (1 bit)
        'u14'  # rs41_airt (14 bits)
        'u10'  # rs41_hum (10 bits)
        'u8'   # rs41_hst (8 bits)
        'u17'  # rs41_pres (17 bits)
        'u1'   # rs41_pcb_h (1 bit)
        'u12'  # tsen_airt (12 bits)
        'u24'  # tsen_ptemp (24 bits)
        'u24'  # tsen_pres (24 bits)
        'u11'  # cpu_temp (11 bits)
    ),
    4: (
        '>'    # little-endian
        'u4'   # rev (4 bits)
        'u1'   # heat_on (1 bit)
        'u9'   # v5 (9 bits)
        'u11'  # v12 (11 bits)
        'u13'  # v56 (13 bits)
        'u11'  # board_t (11 bits)
        'u8'   # temp_setpoint (8 bits)
        'u8'   # switch_mA (8 bits)
        'u1'   # gps_valid (1 bit)
        's32'  # gps_lat (32 bits)
        's32'  # gps_lon (32 bits)
        'u16'  # gps_alt (16 bits)
        'u5'   # gps_sats (5 bits)
        'u19'  # gps_date (19 bits)
        'u25'  # gps_time (25 bits)
        'u8'   # gps_age_secs (8 bits)
        'u1'   # rs41_valid (1 bit)
        'u14'  # rs41_airt (14 bits)
        'u10'  # rs41_hum (10 bits)
        'u8'   # rs41_hst (8 bits)
        'u17'  # rs41_pres (17 bits)
        'u1'   # rs41_pcb_h (1 bit)
        'u12'  # tsen_airt (12 bits)
        'u24'  # tsen_ptemp (24 bits)
        'u24'  # tsen_pres (24 bits)
        'u11'  # cpu_temp (11 bits)
    ),
    5: (
        '>'    # little-endian
        'u4'   # rev (4 bits)
        'u1'   # heat_on (1 bit)
        'u1'   # rs41_en (1 bit)
        'u1'   # tsen_power (1 bit)
        'u9'   # v5 (9 bits)
        'u11'  # v12 (11 bits)
        'u13'  # v56 (13 bits)
        'u11'  # board_t (11 bits)
        'u8'   # temp_setpoint (8 bits)
        'u8'   # switch_mA (8 bits)
        'u1'   # gps_valid (1 bit)
        's32'  # gps_lat (32 bits)
        's32'  # gps_lon (32 bits)
        'u16'  # gps_alt (16 bits)
        'u5'   # gps_sats (5 bits)
        'u19'  # gps_date (19 bits)
        'u25'  # gps_time (25 bits)
        'u8'   # gps_age_secs (8 bits)
        'u1'   # rs41_valid (1 bit)
        'u1'   # rs41_regen (1 bit)
        'u14'  # rs41_airt (14 bits)
        'u10'  # rs41_hum (10 bits)
        'u8'   # rs41_hst (8 bits)
        'u17'  # rs41_pres (17 bits)
        'u1'   # rs41_pcb_h (1 bit)
        'u12'  # tsen_airt (12 bits)
        'u24'  # tsen_ptemp (24 bits)
        'u24'  # tsen_pres (24 bits)
        'u11'  # cpu_temp (11 bits)
    ),
    6: (
        '>'    # little-endian
        'u4'   # rev (4 bits)
        'u4'   # msg_type (4 bits)
        'u8'   # ecu_id (8 bits)
        'u1'   # heat_on (1 bit)
        'u1'   # rs41_en (1 bit)
        'u1'   # tsen_power (1 bit)
        'u9'   # v5 (9 bits)
        'u11'  # v12 (11 bits)
        'u13'  # v56 (13 bits)
        'u11'  # board_t (11 bits)
        'u8'   # temp_setpoint (8 bits)
        'u8'   # switch_mA (8 bits)
        'u1'   # gps_valid (1 bit)
        's32'  # gps_lat (32 bits)
        's32'  # gps_lon (32 bits)
        'u16'  # gps_alt (16 bits)
        'u5'   # gps_sats (5 bits)
        'u19'  # gps_date (19 bits)
        'u25'  # gps_time (25 bits)
        'u8'   # gps_age_secs (8 bits)
        'u1'   # rs41_valid (1 bit)
        'u1'   # rs41_regen (1 bit)
        'u14'  # rs41_airt (14 bits)
        'u10'  # rs41_hum (10 bits)
        'u8'   # rs41_hst (8 bits)
        'u17'  # rs41_pres (17 bits)
        'u8'   # rs41_magXY (8 bits)
        'u1'   # rs41_pcb_h (1 bit)
        'u12'  # tsen_airt (12 bits)
        'u24'  # tsen_ptemp (24 bits)
        'u24'  # tsen_pres (24 bits)
        'u11'  # cpu_temp (11 bits)
    )
}

ecu_field_names = {
    1: [
        'ecu_report_rev', 
        'heat_on', 
        'v5', 
        'v12', 
        'v56', 
        'board_t', 
        'switch_mA', 
        'gps_valid', 
        'gps_lat', 
        'gps_lon', 
        'gps_alt', 
        'gps_sats', 
        'gps_date', 
        'gps_time', 
        'gps_age_secs', 
        'rs41_valid', 
        'rs41_airt', 
        'rs41_hum', 
        'rs41_hst', 
        'rs41_pres', 
        'rs41_pcb_h', 
        'tsen_airt', 
        'tsen_ptemp', 
        'tsen_pres'
    ],
    2: [
        'ecu_report_rev', 
        'heat_on', 
        'v5', 
        'v12', 
        'v56', 
        'board_t', 
        'temp_setpoint',
        'switch_mA', 
        'gps_valid', 
        'gps_lat', 
        'gps_lon', 
        'gps_alt', 
        'gps_sats', 
        'gps_date', 
        'gps_time', 
        'gps_age_secs', 
        'rs41_valid', 
        'rs41_airt', 
        'rs41_hum', 
        'rs41_hst', 
        'rs41_pres', 
        'rs41_pcb_h', 
        'tsen_airt', 
        'tsen_ptemp', 
        'tsen_pres'
    ],
    3: [
        'ecu_report_rev', 
        'heat_on', 
        'v5', 
        'v12', 
        'v56', 
        'board_t', 
        'temp_setpoint',
        'switch_mA', 
        'gps_valid', 
        'gps_lat', 
        'gps_lon', 
        'gps_alt', 
        'gps_sats', 
        'gps_date', 
        'gps_time', 
        'gps_age_secs', 
        'rs41_valid', 
        'rs41_airt', 
        'rs41_hum', 
        'rs41_hst', 
        'rs41_pres', 
        'rs41_pcb_h', 
        'tsen_airt', 
        'tsen_ptemp', 
        'tsen_pres',
        'cpu_temp'
    ],
    4: [
        'ecu_report_rev', 
        'heat_on', 
        'v5', 
        'v12', 
        'v56', 
        'board_t', 
        'temp_setpoint',
        'switch_mA', 
        'gps_valid', 
        'gps_lat', 
        'gps_lon', 
        'gps_alt', 
        'gps_sats', 
        'gps_date', 
        'gps_time', 
        'gps_age_secs', 
        'rs41_valid', 
        'rs41_airt', 
        'rs41_hum', 
        'rs41_hst', 
        'rs41_pres', 
        'rs41_pcb_h', 
        'tsen_airt', 
        'tsen_ptemp', 
        'tsen_pres',
        'cpu_temp'
    ],
    5: [
        'ecu_report_rev', 
        'heat_on', 
        'rs41_en', 
        'tsen_power',
        'v5', 
        'v12', 
        'v56', 
        'board_t', 
        'temp_setpoint',
        'switch_mA', 
        'gps_valid', 
        'gps_lat', 
        'gps_lon', 
        'gps_alt', 
        'gps_sats', 
        'gps_date', 
        'gps_time', 
        'gps_age_secs', 
        'rs41_valid', 
        'rs41_regen',
        'rs41_airt', 
        'rs41_hum', 
        'rs41_hst', 
        'rs41_pres', 
        'rs41_pcb_h', 
        'tsen_airt', 
        'tsen_ptemp', 
        'tsen_pres',
        'cpu_temp'
    ],
    6: [
        'ecu_report_rev', 
        'msg_type',
        'ecu_id',
        'heat_on', 
        'rs41_en', 
        'tsen_power',
        'v5', 
        'v12', 
        'v56', 
        'board_t', 
        'temp_setpoint',
        'switch_mA', 
        'gps_valid', 
        'gps_lat', 
        'gps_lon', 
        'gps_alt', 
        'gps_sats', 
        'gps_date', 
        'gps_time', 
        'gps_age_secs', 
        'rs41_valid', 
        'rs41_regen',
        'rs41_airt', 
        'rs41_hum', 
        'rs41_hst', 
        'rs41_pres', 
        'rs41_magXY',
        'rs41_pcb_h', 
        'tsen_airt', 
        'tsen_ptemp', 
        'tsen_pres',
        'cpu_temp'
    ]
}
