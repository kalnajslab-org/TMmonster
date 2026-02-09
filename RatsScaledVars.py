# Scaled variable functions for RATSReport and ECUReport

def rats_scaled_vars_v0(raw_vars):
    return {
        'rats_report_rev': raw_vars['rats_report_rev'],
        'header_size_bytes': raw_vars['header_size_bytes'],
        'num_ecu_records': raw_vars['num_ecu_records'],
        'ecu_record_size_bytes': raw_vars['ecu_record_size_bytes'],
        'ecu_pwr_on': bool(raw_vars['ecu_pwr_on']),
        'v56': raw_vars['v56'] / 100.0
    }

def rats_scaled_vars_v1(raw_vars):
    return {
        'rats_report_rev': raw_vars['rats_report_rev'],
        'header_size_bytes': raw_vars['header_size_bytes'],
        'num_ecu_records': raw_vars['num_ecu_records'],
        'ecu_record_size_bytes': raw_vars['ecu_record_size_bytes'],
        'ecu_pwr_on': bool(raw_vars['ecu_pwr_on']),
        'v56': raw_vars['v56'] / 100.0,
        'cpu_temp': raw_vars.get('cpu_temp') / 10.0 - 100.0,
        'lora_rssi': raw_vars.get('lora_rssi') / 10.0 - 100.0,
        'lora_snr': raw_vars.get('lora_snr') / 10.0 - 70.0
    }

def rats_scaled_vars_v2(raw_vars):
    return {
        'rats_report_rev': raw_vars['rats_report_rev'],
        'header_size_bytes': raw_vars['header_size_bytes'],
        'num_ecu_records': raw_vars['num_ecu_records'],
        'ecu_record_size_bytes': raw_vars['ecu_record_size_bytes'],
        'ecu_pwr_on': bool(raw_vars['ecu_pwr_on']),
        'v56': raw_vars['v56'] / 100.0,
        'cpu_temp': raw_vars.get('cpu_temp') / 10.0 - 100.0,
        'lora_rssi': raw_vars.get('lora_rssi') / 10.0 - 100.0,
        'lora_snr': raw_vars.get('lora_snr') / 10.0 - 70.0,
        'inst_imon': raw_vars.get('inst_imon') / 10.0
    }

def rats_scaled_vars_v3(raw_vars):
    return {
        'rats_report_rev': raw_vars['rats_report_rev'],
        'rats_id': raw_vars['rats_id'],
        'paired_ecu': raw_vars['paired_ecu'],
        'header_size_bytes': raw_vars['header_size_bytes'],
        'num_ecu_records': raw_vars['num_ecu_records'],
        'ecu_record_size_bytes': raw_vars['ecu_record_size_bytes'],
        'ecu_pwr_on': bool(raw_vars['ecu_pwr_on']),
        'v56': raw_vars['v56'] / 100.0,
        'cpu_temp': raw_vars.get('cpu_temp') / 10.0 - 100.0,
        'lora_rssi': raw_vars.get('lora_rssi') / 10.0 - 100.0,
        'lora_snr': raw_vars.get('lora_snr') / 10.0 - 70.0,
        'inst_imon': raw_vars.get('inst_imon') / 10.0
    }

def ecu_scaled_vars_v1(raw_vars):
    return {
        'ecu_report_rev': raw_vars['ecu_report_rev'],
        'heat_on': bool(raw_vars['heat_on']),
        'v5': raw_vars['v5'] / 100.0,
        'v12': raw_vars['v12'] / 100.0,
        'v56': raw_vars['v56'] / 100.0,
        'board_t': raw_vars['board_t'] / 10.0 - 100.0,
        'switch_mA': raw_vars['switch_mA'],
        'gps_valid': bool(raw_vars['gps_valid']),
        'gps_lat': raw_vars['gps_lat'] * 1.0e-6,
        'gps_lon': raw_vars['gps_lon'] * 1.0e-6,
        'gps_alt': raw_vars['gps_alt'] * 1.0,
        'gps_sats': raw_vars['gps_sats'],
        'gps_date': raw_vars['gps_date'],
        'gps_time': raw_vars['gps_time'],
        'gps_age_secs': raw_vars['gps_age_secs'],
        'rs41_valid': bool(raw_vars['rs41_valid']),
        'rs41_airt': raw_vars['rs41_airt'] / 100.0 - 100.0,
        'rs41_hum': raw_vars['rs41_hum'] / 100.0,
        'rs41_hst': raw_vars['rs41_hst'],
        'rs41_pres': raw_vars['rs41_pres'] / 100.0,
        'rs41_pcb_h': bool(raw_vars['rs41_pcb_h']),
        'tsen_airt': raw_vars['tsen_airt'],
        'tsen_ptemp': raw_vars['tsen_ptemp'],
        'tsen_pres': raw_vars['tsen_pres']
    }

def ecu_scaled_vars_v2(raw_vars):
    return {
        'ecu_report_rev': raw_vars['ecu_report_rev'],
        'heat_on': bool(raw_vars['heat_on']),
        'v5': raw_vars['v5'] / 100.0,
        'v12': raw_vars['v12'] / 100.0,
        'v56': raw_vars['v56'] / 100.0,
        'board_t': raw_vars['board_t'] / 10.0 - 100.0,
        'temp_setpoint': raw_vars['temp_setpoint'] - 100.0,
        'switch_mA': raw_vars['switch_mA'],
        'gps_valid': bool(raw_vars['gps_valid']),
        'gps_lat': raw_vars['gps_lat'] * 1.0e-6,
        'gps_lon': raw_vars['gps_lon'] * 1.0e-6,
        'gps_alt': raw_vars['gps_alt'] * 1.0,
        'gps_sats': raw_vars['gps_sats'],
        'gps_date': raw_vars['gps_date'],
        'gps_time': raw_vars['gps_time'],
        'gps_age_secs': raw_vars['gps_age_secs'],
        'rs41_valid': bool(raw_vars['rs41_valid']),
        'rs41_airt': raw_vars['rs41_airt'] / 100.0 - 100.0,
        'rs41_hum': raw_vars['rs41_hum'] / 100.0,
        'rs41_hst': raw_vars['rs41_hst'],
        'rs41_pres': raw_vars['rs41_pres'] / 100.0,
        'rs41_pcb_h': bool(raw_vars['rs41_pcb_h']),
        'tsen_airt': raw_vars['tsen_airt'],
        'tsen_ptemp': raw_vars['tsen_ptemp'],
        'tsen_pres': raw_vars['tsen_pres']
    }

def ecu_scaled_vars_v3(raw_vars):
    return {
        'ecu_report_rev': raw_vars['ecu_report_rev'],
        'heat_on': bool(raw_vars['heat_on']),
        'v5': raw_vars['v5'] / 100.0,
        'v12': raw_vars['v12'] / 100.0,
        'v56': raw_vars['v56'] / 100.0,
        'board_t': raw_vars['board_t'] / 10.0 - 100.0,
        'temp_setpoint': raw_vars['temp_setpoint'] - 100.0,
        'switch_mA': raw_vars['switch_mA'],
        'gps_valid': bool(raw_vars['gps_valid']),
        'gps_lat': raw_vars['gps_lat'] * 1.0e-6,
        'gps_lon': raw_vars['gps_lon'] * 1.0e-6,
        'gps_alt': raw_vars['gps_alt'] * 1.0,
        'gps_sats': raw_vars['gps_sats'],
        'gps_date': raw_vars['gps_date'],
        'gps_time': raw_vars['gps_time'],
        'gps_age_secs': raw_vars['gps_age_secs'],
        'rs41_valid': bool(raw_vars['rs41_valid']),
        'rs41_airt': raw_vars['rs41_airt'] / 100.0 - 100.0,
        'rs41_hum': raw_vars['rs41_hum'] / 100.0,
        'rs41_hst': raw_vars['rs41_hst'],
        'rs41_pres': raw_vars['rs41_pres'] / 100.0,
        'rs41_pcb_h': bool(raw_vars['rs41_pcb_h']),
        'tsen_airt': raw_vars['tsen_airt'],
        'tsen_ptemp': raw_vars['tsen_ptemp'],
        'tsen_pres': raw_vars['tsen_pres'],
        'cpu_temp': raw_vars.get('cpu_temp')/10 - 100.0
    }

def ecu_scaled_vars_v4(raw_vars):
    return {
        'ecu_report_rev': raw_vars['ecu_report_rev'],
        'heat_on': bool(raw_vars['heat_on']),
        'v5': raw_vars['v5'] / 100.0,
        'v12': raw_vars['v12'] / 100.0,
        'v56': raw_vars['v56'] / 100.0,
        'board_t': raw_vars['board_t'] / 10.0 - 100.0,
        'temp_setpoint': raw_vars['temp_setpoint'] - 100.0,
        'switch_mA': raw_vars['switch_mA'],
        'gps_valid': bool(raw_vars['gps_valid']),
        'gps_lat': raw_vars['gps_lat'] * 1.0e-6,
        'gps_lon': raw_vars['gps_lon'] * 1.0e-6,
        'gps_alt': raw_vars['gps_alt'] * 1.0,
        'gps_sats': raw_vars['gps_sats'],
        'gps_date': raw_vars['gps_date'],
        'gps_time': raw_vars['gps_time'],
        'gps_age_secs': raw_vars['gps_age_secs'],
        'rs41_valid': bool(raw_vars['rs41_valid']),
        'rs41_airt': raw_vars['rs41_airt'] / 100.0 - 100.0,
        'rs41_hum': raw_vars['rs41_hum'] / 100.0,
        'rs41_hst': raw_vars['rs41_hst'],
        'rs41_pres': raw_vars['rs41_pres'] / 100.0,
        'rs41_pcb_h': bool(raw_vars['rs41_pcb_h']),
        'tsen_airt': raw_vars['tsen_airt'],
        'tsen_ptemp': raw_vars['tsen_ptemp'],
        'tsen_pres': raw_vars['tsen_pres'],
        'cpu_temp': raw_vars.get('cpu_temp')/10 - 100.0
    }

def ecu_scaled_vars_v5(raw_vars):
    return {
        'ecu_report_rev': raw_vars['ecu_report_rev'],
        'heat_on': bool(raw_vars['heat_on']),
        'rs41_en': bool(raw_vars['rs41_en']),
        'tsen_power': bool(raw_vars['tsen_power']),
        'v5': raw_vars['v5'] / 100.0,
        'v12': raw_vars['v12'] / 100.0,
        'v56': raw_vars['v56'] / 100.0,
        'board_t': raw_vars['board_t'] / 10.0 - 100.0,
        'temp_setpoint': raw_vars['temp_setpoint'] - 100.0,
        'switch_mA': raw_vars['switch_mA'],
        'gps_valid': bool(raw_vars['gps_valid']),
        'gps_lat': raw_vars['gps_lat'] * 1.0e-6,
        'gps_lon': raw_vars['gps_lon'] * 1.0e-6,
        'gps_alt': raw_vars['gps_alt'] * 1.0,
        'gps_sats': raw_vars['gps_sats'],
        'gps_date': raw_vars['gps_date'],
        'gps_time': raw_vars['gps_time'],
        'gps_age_secs': raw_vars['gps_age_secs'],
        'rs41_valid': bool(raw_vars['rs41_valid']),
        'rs41_regen': bool(raw_vars['rs41_regen']),
        'rs41_airt': raw_vars['rs41_airt'] / 100.0 - 100.0,
        'rs41_hum': raw_vars['rs41_hum'] / 100.0,
        'rs41_hst': raw_vars['rs41_hst'],
        'rs41_pres': raw_vars['rs41_pres'] / 100.0,
        'rs41_pcb_h': bool(raw_vars['rs41_pcb_h']),
        'tsen_airt': raw_vars['tsen_airt'],
        'tsen_ptemp': raw_vars['tsen_ptemp'],
        'tsen_pres': raw_vars['tsen_pres'],
        'cpu_temp': raw_vars.get('cpu_temp')/10 - 100.0
    }

def ecu_scaled_vars_v6(raw_vars):
    return {
        'ecu_report_rev': raw_vars['ecu_report_rev'],
        'msg_type': raw_vars['msg_type'],
        'ecu_id': raw_vars['ecu_id'],
        'heat_on': bool(raw_vars['heat_on']),
        'rs41_en': bool(raw_vars['rs41_en']),
        'tsen_power': bool(raw_vars['tsen_power']),
        'v5': raw_vars['v5'] / 100.0,
        'v12': raw_vars['v12'] / 100.0,
        'v56': raw_vars['v56'] / 100.0,
        'board_t': raw_vars['board_t'] / 10.0 - 100.0,
        'temp_setpoint': raw_vars['temp_setpoint'] - 100.0,
        'switch_mA': raw_vars['switch_mA'],
        'gps_valid': bool(raw_vars['gps_valid']),
        'gps_lat': raw_vars['gps_lat'] * 1.0e-6,
        'gps_lon': raw_vars['gps_lon'] * 1.0e-6,
        'gps_alt': raw_vars['gps_alt'] * 1.0,
        'gps_sats': raw_vars['gps_sats'],
        'gps_date': raw_vars['gps_date'],
        'gps_time': raw_vars['gps_time'],
        'gps_age_secs': raw_vars['gps_age_secs'],
        'rs41_valid': bool(raw_vars['rs41_valid']),
        'rs41_regen': bool(raw_vars['rs41_regen']),
        'rs41_airt': raw_vars['rs41_airt'] / 100.0 - 100.0,
        'rs41_hum': raw_vars['rs41_hum'] / 100.0,
        'rs41_hst': raw_vars['rs41_hst'],
        'rs41_pres': raw_vars['rs41_pres'] / 100.0,
        'rs41_pcb_h': bool(raw_vars['rs41_pcb_h']),
        'tsen_airt': raw_vars['tsen_airt'],
        'tsen_ptemp': raw_vars['tsen_ptemp'],
        'tsen_pres': raw_vars['tsen_pres'],
        'cpu_temp': raw_vars.get('cpu_temp')/10 - 100.0
    }
