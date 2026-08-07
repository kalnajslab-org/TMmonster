#
# See StratoCore_RATS/src/RATSReport.h which describes the bit-packed 
# RATSReport header block.
#
# See ECUComm/src/ECUComm.h for ECUComm::ECUReport_t, which describes the
# bit-packed ECU data block.
# 

import sys
import json
import traceback
import xmltodict
import argparse
import os
from importlib.metadata import version, PackageNotFoundError
from . import registry
from . import builtin_decoders  # noqa: F401  (imported for its registration side effects)
from .registry import DecodeContext
from .tm import binary_crc

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
    try:
        pkg_version = version("tmmonster")
    except PackageNotFoundError:
        pkg_version = "unknown"
    parser = argparse.ArgumentParser(
        description="Decode Strateole2 TM binary files (RATS, RACHUTS, RPU, ECU, LPC, MCB).",
        epilog=(
            "To process files in bulk, grouped into time windows, "
            "see the companion tool: tmmonster-batch --help"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {pkg_version}")
    parser.add_argument("--report-type", type=str, default=None, help="Specify the type of report to process (e.g., RATSREPORT). If not specified, all report types will be processed.")
    parser.add_argument("tm_file", nargs='+', help="Path(s) to the TM file(s) or directories")
    parser.add_argument("--headers", action="store_true", help="Print TM XML section and report headers")
    parser.add_argument("--payload", action="store_true", help="Print the decoded payload")
    parser.add_argument("--summary", action="store_true", help="Print a single line summary for each file")
    parser.add_argument("--absolute-paths", action="store_true", help="Print absolute file paths in summary view (default: filename only)")
    parser.add_argument("--csv", action="store_true", help="Output the payload values in CSV format")
    parser.add_argument("--float-format", type=str, help="Format string for printing CSV floats (e.g., .3f, .6g)")
    parser.add_argument("--count", action="store_true", help="Print a JSON tally of report types encountered")
    args = parser.parse_args()

    # Expand directories to include all files (not directories) inside them
    expanded_files = []
    for path in args.tm_file:
        if os.path.isdir(path):
            # Sort entries so files are processed in name order. The TM
            # filenames are zero-padded ISO-style timestamps, so name order is
            # chronological order.
            for entry in sorted(os.listdir(path)):
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
    tm_start = all_bytes.find(b"<TM>")
    if tm_start == -1:
        print("<TM> not found")
        return {}
    tm_end = all_bytes.find(b"</TM>")
    if tm_end == -1:
        print("</TM> not found")
        return {}
    tm_end += 5  # include the </TM> tag
    tm_str = all_bytes[tm_start:tm_end].decode('utf-8')
    xml_dict = xmltodict.parse(tm_str)

    crc_start = all_bytes.find(b"<CRC>")
    if crc_start == -1:
        print("<CRC> not found")
        return {}
    crc_end = all_bytes.find(b"</CRC>")
    if crc_end == -1:
        print("</CRC> not found")
        return {}
    crc_end += 6  # include the </CRC> tag
    crc_dict = xmltodict.parse(all_bytes[crc_start:crc_end].decode('utf-8'))
    if crc_dict:
        xml_dict['CRC'] = crc_dict.get('CRC', {})

    return xml_dict

def make_summary(xml_dict: dict, file_path: str) -> str:
    """
    Generates a single-line JSON summary for the given TM XML dictionary.
    """
    tm_section = xml_dict.get('TM', {})
    record = {
        "Inst":       tm_section.get('Inst'),
        "Msg":        tm_section.get('Msg', ''),
        "StateMess1": tm_section.get('StateMess1', ''),
        "StateFlag1": tm_section.get('StateFlag1', ''),
        "StateMess2": tm_section.get('StateMess2', ''),
        "StateFlag2": tm_section.get('StateFlag2', ''),
        "StateMess3": tm_section.get('StateMess3', ''),
        "StateFlag3": tm_section.get('StateFlag3', ''),
        "Length":     int(tm_section.get('Length', '0')),
        "CRC":        xml_dict.get('CRC'),
        "FilePath":   file_path,
    }
    return json.dumps(record, separators=(',', ':'))

def get_report_type(xml_dict: dict) -> str | None:
    """
    Determines the report type from the TM XML dictionary.
    """

    instrument = xml_dict['TM']['Inst']
    if instrument == "RATS":
        return xml_dict['TM']['StateMess1']
    elif instrument == "LPC":
        if xml_dict['TM']['StateMess2'] == "RS41":
            return "LPCRS41"
        else:
            return "LPCOPC"
    elif instrument == "RACHUTS":
        return xml_dict['TM']['StateMess1']

    return None

def run_decoder(report_type: str | None, tm_filename: str, tm_file, args, csv_header_printed: set, xml_dict: dict) -> set:
    """
    Runs the registered decoder for the given report type (see builtin_decoders
    for the adapters). Each decoder reads the binary payload from the file
    itself via TMmsg; here we only tell it whether a payload exists. Returns the
    updated set of report types that have already printed a CSV header.
    """
    decoder = registry.get(report_type)
    if decoder is None:
        if args.payload:
            print(f"{report_type} payload processing not yet implemented.")
        return csv_header_printed

    ctx = DecodeContext(
        report_type=report_type,
        has_payload=xml_dict['TM'].get('Length', '0') != '0',
        headers=args.headers,
        show_payload=args.payload,
        csv=args.csv,
        float_format=args.float_format,
        xml_dict=xml_dict,
        tm_filename=tm_filename,
        tm_file=tm_file,
        first_file=report_type not in csv_header_printed,
    )

    decoder(ctx)

    # Only record the header as printed once a decoder has actually emitted it,
    # so a first file that produced no header (e.g. a records-less RATSREPORT)
    # doesn't suppress it for the rest of the batch.
    if args.csv and ctx.header_emitted:
        csv_header_printed.add(report_type)

    return csv_header_printed

def main(args):
    csv_header_printed: set[str] = set()
    counts: dict[str, int] = {}

    for filename in args.tm_file:
        tm_filename = os.path.abspath(filename)
        with open(tm_filename, "rb") as tm_file:
            try:
                # Read the entire file
                all_bytes = tm_file.read()

                xml_dict = extractTMxml(all_bytes)
                if not xml_dict:
                    continue

                # Find the report type in this TM
                report_type = get_report_type(xml_dict)
                counts[report_type or "UNKNOWN"] = counts.get(report_type or "UNKNOWN", 0) + 1

                # Only process the report type(s) specified by the user. 
                # If no report type is specified, process all report types.
                if not args.report_type or args.report_type in report_type:

                    # Verify the binary-section CRC (REQ 523): 2 big-endian bytes
                    # after the data block. A mismatch means the payload was
                    # corrupted in transit; warn but still attempt to decode.
                    if xml_dict['TM'].get('Length', '0') != '0':
                        ln = int(xml_dict['TM']['Length'])
                        st = all_bytes.find(b'</CRC>\nSTART') + 12
                        stored = all_bytes[st+ln:st+ln+2]
                        if len(stored) == 2 and binary_crc(all_bytes[st:st+ln]) != int.from_bytes(stored, 'big'):
                            print(f"Warning: binary CRC mismatch in {os.path.basename(tm_file.name)}", file=sys.stderr)

                    if args.summary:
                        file_label = tm_file.name if args.absolute_paths else os.path.basename(tm_file.name)
                        print(make_summary(xml_dict, file_label))

                    if args.headers:
                        print("----- TM XML section:")
                        for key, value in xml_dict['TM'].items():
                            print(f'{key}: {value}')
                        print()

                    # Perform the appropriate decoding for this report type, if
                    # implemented. Decoders read the binary payload from the file
                    # themselves via TMmsg.
                    csv_header_printed = run_decoder(report_type, tm_filename, tm_file, args, csv_header_printed, xml_dict)
            except BrokenPipeError:
                # Downstream reader (e.g. `| head`) closed the pipe early.
                # There's no point continuing to decode remaining files, and
                # every further print() would just raise the same error;
                # propagate it so cli_main can exit quietly.
                raise
            except Exception as e:
                print(f"Error processing file {tm_file.name}: {e}", file=sys.stderr)
                exc_type, exc_value, exc_tb = sys.exc_info()
                tb_entries = traceback.extract_tb(exc_tb) if exc_tb else []
                if tb_entries:
                    last = tb_entries[-1]
                    print(
                        f"Exception origin: {last.filename}:{last.lineno}",
                        file=sys.stderr,
                    )
                    if last.line:
                        print(f"Python line: {last.line.strip()}", file=sys.stderr)
                print("Traceback:", file=sys.stderr)
                traceback.print_exception(exc_type, exc_value, exc_tb, file=sys.stderr)

    return counts

def cli_main():
    args = parse_args()
    try:
        counts = main(args)
    except BrokenPipeError:
        # Redirect stdout to devnull before exiting so the interpreter's
        # shutdown-time flush doesn't raise the same error again (standard
        # recipe for handling SIGPIPE-equivalent behavior on all platforms).
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)
    if args.count:
        print(json.dumps(counts, indent=2))

if __name__ == "__main__":
    cli_main()
