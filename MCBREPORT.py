import bitstruct
from datetime import datetime, timezone
import math

mcb_start_time = (
    '>'     # little-endian
    'u32'   # start time epoch seconds
)
mcb_start_field_names = [
    'start_time_epoch'
]

mcb_bits = (
    '>'     # little-endian
    'u8'    # sync byte 0xA5
    'u16'   # tenths of seconds since start
    'u8'    # rotating parameter index
    'u16'   # rotating parameter average
    'u16'   # rotating parameter max
    'u16'   # reel torque average
    'u16'   # reel torque max
    'u16'   # level wind torque average
    'u16'   # level wind torque max
    'u16'   # reel current average
    'u16'   # reel current max
    'u16'   # level wind current average
    'u16'   # level wind current max
    'f32'   # reel absolute position in revolutions
    'f32'   # level wind absolute position in whatever units the level wind uses
)

mcb_field_names = [
    'sync_byte',
    'elapsed_time_tenths_sec',
    'rotating_parameter_id',
    'rotating_parameter_avg',
    'rotating_parameter_max',
    'reel_torque_avg',
    'reel_torque_max',
    'level_wind_torque_avg',
    'level_wind_torque_max',
    'reel_current_avg',
    'reel_current_max',
    'level_wind_current_avg',
    'level_wind_current_max',
    'reel_position',
    'level_wind_position'
]

def csv_header():
    header_fields = ','.join(mcb_start_field_names+['start_time_iso']+mcb_field_names)
    return header_fields

def decode_payload(payload, csv_output=False):

    # From StratoRATS::InitMCBMotionTracking():
    # uint32_t ProfileStartEpoch  = now();
    # MCB_TM_buffer[MCB_TM_buffer_idx++] = (uint8_t) (ProfileStartEpoch >> 24);
    # MCB_TM_buffer[MCB_TM_buffer_idx++] = (uint8_t) (ProfileStartEpoch >> 16);
    # MCB_TM_buffer[MCB_TM_buffer_idx++] = (uint8_t) (ProfileStartEpoch >> 8);
    # MCB_TM_buffer[MCB_TM_buffer_idx++] = (uint8_t) (ProfileStartEpoch & 0xFF);

    # From StratoRATS::AddMCBTM():
    # MCB_TM_buffer[MCB_TM_buffer_idx++] = (uint8_t) 0xA5;
    # // tenths of seconds since start
    # uint16_t elapsed_time = (uint16_t)((millis() - reel_motion_start) / 100);
    # MCB_TM_buffer[MCB_TM_buffer_idx++] = (uint8_t) (elapsed_time >> 8);
    # MCB_TM_buffer[MCB_TM_buffer_idx++] = (uint8_t) (elapsed_time & 0xFF);

    # From MonitorMCB::SendMotionData(void):
    # buffer_success &= BufferAddUInt8(rotating_parameter, tm_buffer, MOTION_TM_SIZE, &buffer_index);
    # buffer_success &= BufferAddUInt16(AverageResetSlowTM((RotatingParam_t) rotating_parameter), tm_buffer, MOTION_TM_SIZE, &buffer_index);
    # buffer_success &= BufferAddUInt16(slow_tm[rotating_parameter].running_max, tm_buffer, MOTION_TM_SIZE, &buffer_index);
    # buffer_success &= BufferAddUInt16(AverageResetFastTM(&reel_torques), tm_buffer, MOTION_TM_SIZE, &buffer_index);
    # buffer_success &= BufferAddUInt16(reel_torques.running_max, tm_buffer, MOTION_TM_SIZE, &buffer_index);
    # buffer_success &= BufferAddUInt16(AverageResetFastTM(&lw_torques), tm_buffer, MOTION_TM_SIZE, &buffer_index);
    # buffer_success &= BufferAddUInt16(lw_torques.running_max, tm_buffer, MOTION_TM_SIZE, &buffer_index);
    # buffer_success &= BufferAddUInt16(AverageResetFastTM(&reel_currents), tm_buffer, MOTION_TM_SIZE, &buffer_index);
    # buffer_success &= BufferAddUInt16(reel_currents.running_max, tm_buffer, MOTION_TM_SIZE, &buffer_index);
    # buffer_success &= BufferAddUInt16(AverageResetFastTM(&lw_currents), tm_buffer, MOTION_TM_SIZE, &buffer_index);
    # buffer_success &= BufferAddUInt16(lw_currents.running_max, tm_buffer, MOTION_TM_SIZE, &buffer_index);
    # buffer_success &= BufferAddFloat(reel->absolute_position / REEL_UNITS_PER_REV, tm_buffer, MOTION_TM_SIZE, &buffer_index);
    # buffer_success &= BufferAddFloat(levelWind->absolute_position, tm_buffer, MOTION_TM_SIZE, &buffer_index);

    records_size_bytes = math.ceil(bitstruct.calcsize(mcb_bits) / 8)
    num_records = len(payload) // records_size_bytes
    if num_records == 0:
        return

    start_time_vars = bitstruct.unpack_dict(mcb_start_time, mcb_start_field_names, payload[:4])
    utc_dt_object = datetime.fromtimestamp(int(start_time_vars['start_time_epoch']), tz=timezone.utc)
    iso_format_utc = utc_dt_object.isoformat()+'Z'

    if not csv_output:
        print(f"Tracking start time (UTC): {iso_format_utc}")

    for i in range(4, len(payload), records_size_bytes):
        record = payload[i:i+records_size_bytes]
        vars = bitstruct.unpack_dict(mcb_bits, mcb_field_names, record)
        if csv_output:
            csv_values = iso_format_utc
            csv_values += ',' + ','.join(str(start_time_vars[field]) for field in mcb_start_field_names)
            csv_values += ',' + ','.join(str(vars[field]) for field in mcb_field_names)
            print(f"{csv_values}")
        else:
            print(f"--- MCB record {i//records_size_bytes} of {num_records} ---")
            for key, value in vars.items():
                print(f"{key}: {value}")
