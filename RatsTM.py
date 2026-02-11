#
# See StratoCore_RATS/src/RATSReport.h which describes the bit-packed 
# RATSReport header block.
#
# See ECUComm/src/ECUComm.h for ECUComm::ECUReport_t, which describes the
# bit-packed ECU data block.
# 

import sys
import xmltodict
import argparse
import os
import RATSREPORT
import RATSTCACK
import MCBREPORT

# The RATSReport contains a bit-packed RATSReport header and a series of ECUReports.
#
# The RATSReport and ECUReports have revision numbers, which are stored in the first 4 bits of the record.

# The general scheme for unpacking the bit packed data for the RATSReport and ECUReports 
# is the same, and utilize the bitstruct library.
#
# A "*_bits" dictionary is defined for each version of the RATSReport and ECUReport. These
# correspond to the C structures defined the C++ header files. When a new version is added,
# add a new entry to the "_bits" dictionary with the bitstruct format string for that version.
# The format strings are defined in RatsBitDefs.py.
#
# Similarly, a "*_field_names" dictionary is defined for each version of the RATSReport and ECUReport.
# These correspond to the field names in the C++ header files. When a new version is added, 
# add a new entry to the "_field_names" dictionary with the field names for that version.
# The field name lists are defined in RatsBitDefs.py.
#
# Finally, scaling functions "*_scaled_vars_v<rev>" are defined for each version of the RATSReport and ECUReport.
# These functions take the raw data unpacked from the bit-packed format and scale it to human-readable units.
# The scaling functions are defined in RatsScaledVars.py.

def parse_args():
    parser = argparse.ArgumentParser(description="Decode RATS TM binary files.")
    parser.add_argument("--report-type", type=str, default=None, help="Specify the type of report to process (e.g., RATSREPORT). If not specified, all report types will be processed.")
    parser.add_argument("tm_file", nargs='+', help="Path(s) to the TM file(s) or directories")
    parser.add_argument("--headers", action="store_true", help="Print TM XML section and report headers")
    parser.add_argument("--payload", action="store_true", help="Print the decoded payload")
    parser.add_argument("--summary", action="store_true", help="Print a single line summary for each file")
    parser.add_argument("--csv", action="store_true", help="Output the payload values in CSV format")
    parser.add_argument("--float-format", type=str, help="Format string for printing CSV floats (e.g., .3f, .6g)")
    args = parser.parse_args()

    # Expand directories to include all files (not directories) inside them
    expanded_files = []
    for path in args.tm_file:
        if os.path.isdir(path):
            for entry in os.listdir(path):
                full_path = os.path.join(path, entry)
                if os.path.isfile(full_path):
                    expanded_files.append(full_path)
        else:
            expanded_files.append(path)
    args.tm_file = expanded_files
    return args

def extractTMxml(all_bytes: bytes) -> dict:
    """
    Extracts and parses the <TM>...</TM> XML section from the given bytes.
    Returns the parsed XML as a dictionary.
    """
    xml_start = all_bytes.find(b"<TM>")
    if xml_start == -1:
        print("XML section start not found")
        return {}
    xml_end = all_bytes.find(b"</TM>")
    if xml_end == -1:
        print("XML section not found")
        return {}
    xml_end += 5  # include the </TM> tag
    xml_str = all_bytes[xml_start:xml_end].decode('utf-8')
    xml_dict = xmltodict.parse(xml_str)
    return xml_dict

def make_summary(xml_dict: dict, file_path: str) -> str:
    """
    Generates a single line CSV summary for the given TM XML dictionary.
    """
    tm_section = xml_dict.get('TM', {})
    state_mess1 = tm_section.get('StateMess1', '')
    state_flag1 = tm_section.get('StateFlag1', '')
    state_mess2 = tm_section.get('StateMess2', '')
    state_flag2 = tm_section.get('StateFlag2', '')
    state_mess3 = tm_section.get('StateMess3', '')
    state_flag3 = tm_section.get('StateFlag3', '')
    length = int(tm_section.get('Length', '0'))

    summary = ''
    summary += f'\"{state_mess1}\",\"{state_flag1}\",'
    summary += f'\"{state_mess2}\",\"{state_flag2}\",'
    summary += f'\"{state_mess3}\",\"{state_flag3}\",'
    summary += f'{length},'
    summary += f'\"{file_path}\"'
    return summary

def main(args):
    first_file = True

    for tm_file in args.tm_file:
        tm_file = os.path.abspath(tm_file)
        with open(tm_file, "rb") as tm_file:
            try:
                # Read the entire file
                all_bytes = tm_file.read()

                xml_dict = extractTMxml(all_bytes)
                if not xml_dict:
                    continue

                # Find the report type in this TM
                report_type = xml_dict['TM']['StateMess1']

                # Only process the report type(s) specified by the user. 
                # If no report type is specified, process all report types.
                if not args.report_type or args.report_type in report_type:

                    if args.summary:
                        print(make_summary(xml_dict, tm_file.name))

                    if args.headers:
                        print("----- TM XML section:")
                        for key, value in xml_dict['TM'].items():
                            print(f'{key}: {value}')
                        print()

                    # Get the payload, if it exists.
                    payload = None
                    if xml_dict['TM']['Length'] != '0':
                        payload_start = all_bytes.find(b"START") + 5
                        if payload_start != -1:
                            payload = all_bytes[payload_start:-5]  # Exclude the CRC and "END" marker

                    payload_processed = False

                    # Process the payload based on the report type
                    if report_type == "RATSREPORT":
                        if (args.payload or args.headers) and not payload:
                                print(f"Binary payload not found for {report_type}, can't read headers or data")
                                continue
                        if payload:
                            RATSREPORT.decode_payload(payload,args.headers, args.payload, first_file, args.csv, args.float_format)
                        payload_processed = True

                    if report_type == "RATSTCACK":
                        if args.payload and not payload:
                                continue
                        if args.payload:
                            RATSTCACK.decode_payload(payload, args.headers, args.payload, first_file, args.csv)
                        payload_processed = True

                    if report_type == "RATSTEXT":
                        if args.payload and not payload:
                                continue
                        if args.payload:
                            RATSTCACK.decode_payload(payload, args.headers, args.payload, first_file, args.csv)
                        payload_processed = True

                    if report_type == "MCBREPORT":
                        if first_file and args.csv:
                            print(MCBREPORT.csv_header())
                            first_file = False
                        if args.payload and not payload:
                                continue
                        if args.payload:
                            MCBREPORT.decode_payload(payload, args.csv, args.float_format)
                        payload_processed = True

                    if args.payload and not payload_processed:
                        print(f"{report_type} payload processing not yet implemented.")
            except Exception as e:
                print(f"Error processing file {tm_file.name}: {e}", file=sys.stderr)

if __name__ == "__main__":
    args = parse_args()
    main(args)