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
import RATSReport

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
    parser.add_argument("tm_file", nargs='+', help="Path(s) to the TM file(s) or directories")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--header-only", action="store_true", help="Print TM XML section and report headers only, without data records")
    group.add_argument("--summary", action="store_true", help="Print a single line summary for each file")
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
    state_mess1 = tm_section.get('StateMess1', 'N/A')
    state_flag1 = tm_section.get('StateFlag1', 'N/A')
    state_mess2 = tm_section.get('StateMess2', 'N/A')
    state_flag2 = tm_section.get('StateFlag2', 'N/A')
    state_mess3 = tm_section.get('StateMess3', 'N/A')
    state_flag3 = tm_section.get('StateFlag3', 'N/A')
    length = tm_section.get('Length', 'N/A')

    summary = ''
    summary += f'\"{state_mess1}\",\"{state_flag1}\",'
    summary += f'\"{state_mess2}\",\"{state_flag2}\",'
    summary += f'\"{state_mess3}\",\"{state_flag3}\",'
    summary += f'{length},'
    summary += f'\"{file_path}\"'
    return summary

def main(args):
    header_only = args.header_only

    for tm_file in args.tm_file:

        with open(tm_file, "rb") as tm_file:

            # Read the entire file
            all_bytes = tm_file.read()

            xml_dict = extractTMxml(all_bytes)
            if not xml_dict:
                continue

            print(make_summary(xml_dict, tm_file.name))

            if args.summary:
                continue

            print("----- TM XML section:")
            for key, value in xml_dict['TM'].items():
                print(f'{key}: {value}')
            print()

            if any(key in xml_dict['TM']['StateMess1'] for key in ['RATSReport', 'RATSREPORT']):
                # Find the start of the binary payload
                bin_start = all_bytes.find(b"START")+5
                if bin_start == -1:
                    print("Binary payload not found")
                    continue
                RATSReport.decode_ratsreport(all_bytes, bin_start, header_only)
            else:
                print("No RATSREPORT section found in TM XML")

if __name__ == "__main__":
    args = parse_args()
    main(args)