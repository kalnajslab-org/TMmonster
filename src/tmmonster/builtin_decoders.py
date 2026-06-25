"""
Built-in decoder adapters.

Importing this module registers every report-type decoder shipped with
tmmonster. Each adapter is a faithful translation of what the old run_decoder
if/elif ladder did for that report type — the per-decoder modules themselves are
unchanged. The dispatcher (TMmonster.run_decoder) handles the bookkeeping common
to all report types (first-file tracking and recording that a CSV header has
been emitted), so adapters only express what is specific to their decoder.
"""

from . import RATSREPORT
from . import RATSTCACK
from . import RATSEEPROM
from . import MCBREPORT
from . import MCBEEPROM
from . import LPCRS41
from . import LPCOPC
from . import RPUREPORT
from . import RPUSTATUS
from . import RATCHUTSEEPROM
from .registry import register, DecodeContext


@register("RATSREPORT")
def _rats_report(ctx: DecodeContext) -> None:
    if (ctx.show_payload or ctx.headers) and ctx.payload is None:
        print("Binary payload not found for RATSREPORT, can't read headers or data")
        return
    if ctx.payload is not None:
        RATSREPORT.decode_payload(ctx.payload, ctx.headers, ctx.show_payload,
                                  ctx.first_file, ctx.csv, ctx.float_format)


@register("RATSTCACK", "RATSTEXT")
def _rats_tcack(ctx: DecodeContext) -> None:
    if ctx.show_payload:
        if ctx.payload is None:
            return
        RATSTCACK.decode_payload(ctx.payload, ctx.headers, ctx.show_payload,
                                 ctx.first_file, ctx.csv)


@register("RATSEEPROM")
def _rats_eeprom(ctx: DecodeContext) -> None:
    if ctx.show_payload:
        if ctx.payload is None:
            return
        RATSEEPROM.decode_payload(ctx.payload, ctx.headers, ctx.show_payload,
                                  ctx.first_file, ctx.csv, ctx.float_format)


@register("MCBEEPROM")
def _mcb_eeprom(ctx: DecodeContext) -> None:
    if ctx.show_payload:
        if ctx.payload is None:
            return
        MCBEEPROM.decode_payload(ctx.payload, ctx.headers, ctx.show_payload,
                                 ctx.first_file, ctx.csv, ctx.float_format)


@register("RATCHUTSEEPROM")
def _ratchuts_eeprom(ctx: DecodeContext) -> None:
    if ctx.show_payload:
        if ctx.payload is None:
            return
        RATCHUTSEEPROM.decode_payload(ctx.payload, ctx.headers, ctx.show_payload,
                                      ctx.first_file, ctx.csv, ctx.float_format)


@register("LPCRS41")
def _lpc_rs41(ctx: DecodeContext) -> None:
    ctx.tm_file.close()  # close so RS41msg can reopen the file by name
    if ctx.show_payload:
        if ctx.payload is None:
            return
        LPCRS41.decode_payload(ctx.tm_filename, ctx.headers, ctx.show_payload,
                               ctx.first_file, ctx.csv, ctx.float_format)


@register("LPCOPC")
def _lpc_opc(ctx: DecodeContext) -> None:
    if ctx.show_payload:
        if ctx.payload is None:
            return
        LPCOPC.decode_payload(ctx.tm_filename, ctx.headers, ctx.show_payload,
                              ctx.first_file, ctx.csv, ctx.float_format)


@register("MCBREPORT")
def _mcb_report(ctx: DecodeContext) -> None:
    if ctx.first_file and ctx.csv:
        print(MCBREPORT.csv_header())
    if ctx.show_payload:
        if ctx.payload is None:
            return
        MCBREPORT.decode_payload(ctx.payload, ctx.csv, ctx.float_format)


@register("RPUREPORT")
def _rpu_report(ctx: DecodeContext) -> None:
    if ctx.first_file and ctx.csv:
        print(RPUREPORT.csv_header())
    if ctx.show_payload:
        if ctx.payload is None:
            return
        # The profile start reference (epoch, lat, lon) is carried in the TM's
        # StateMess3 and the profile number in StateMess2.
        tm = ctx.xml_dict['TM']
        start = RPUREPORT.parse_start_values(tm.get('StateMess3'))
        profile = RPUREPORT.parse_profile(tm.get('StateMess2'))
        RPUREPORT.decode_payload(ctx.payload, ctx.csv, ctx.float_format, start, profile)


@register("RPUSTATUS")
def _rpu_status(ctx: DecodeContext) -> None:
    if ctx.show_payload or ctx.headers:
        if ctx.payload is None:
            print("Binary payload not found for RPUSTATUS, can't read headers or data")
            return
        RPUSTATUS.decode_payload(ctx.payload, ctx.headers, ctx.show_payload,
                                 ctx.first_file, ctx.csv, ctx.float_format)
