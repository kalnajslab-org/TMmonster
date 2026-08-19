"""
Decoder registry for tmmonster.

Each report type is handled by a small adapter function registered under its
report-type string. The CLI looks the adapter up by report type instead of
walking a long if/elif ladder, so adding a decoder no longer means editing the
dispatcher.

An adapter receives a DecodeContext carrying everything a decoder might need
(the binary payload, the parsed TM XML, output-mode flags, the source file).
Each adapter owns its own quirks (whether it runs on --headers as well as
--payload, whether it prints a CSV header on the first file, whether it reopens
the file, etc.); the dispatcher only handles the bookkeeping common to all.
"""

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class DecodeContext:
    report_type: str
    has_payload: bool             # True if the TM carries a binary payload (Length != 0)
    headers: bool                 # --headers requested
    show_payload: bool            # --payload requested
    csv: bool                     # --csv requested
    float_format: Optional[str]   # --float-format value
    xml_dict: dict                # parsed TM XML (TM/CRC sections)
    tm_filename: str              # absolute path to the source TM file
    tm_file: object               # the open file handle for the source TM
    first_file: bool = False      # first file seen for this report type
    file_number: int = 0          # 1-based count of files of this report type decoded in this run
    # Whether this file emitted the one-time CSV column header. Defaults True
    # (most decoders always emit their header on the first file); a decoder
    # that can fail to emit it — e.g. a records-less RATSREPORT — sets it False
    # so the dispatcher does not prematurely mark the header as printed.
    header_emitted: bool = True


# report-type string -> adapter
DECODERS: dict[str, Callable[["DecodeContext"], None]] = {}


def register(*report_types: str):
    """Decorator registering an adapter for one or more report-type strings."""
    def decorate(fn: Callable[["DecodeContext"], None]):
        for report_type in report_types:
            DECODERS[report_type] = fn
        return fn
    return decorate


def get(report_type: Optional[str]) -> Optional[Callable[["DecodeContext"], None]]:
    return DECODERS.get(report_type)
