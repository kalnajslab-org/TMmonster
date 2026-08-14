"""
Built-in decoder adapters.

Importing this module registers every report-type decoder shipped with
tmmonster. Each decoder takes the TM filename and pulls its binary payload via
the TMmsg class (see decoders/*.py); the adapters below wire the CLI's
DecodeContext to each decoder's call signature and express what is specific to
that decoder (whether it runs on --headers, whether it prints a CSV header on
the first file, etc.). The dispatcher (cli.run_decoder) handles the bookkeeping
common to all report types.
"""

from . import tm  # noqa: F401  (ensures the TMmsg module is importable here)
from .decoders import rats_report
from .decoders import rats_tcack
from .decoders import rats_eeprom
from .decoders import mcb_report
from .decoders import mcb_eeprom
from .decoders import lpc_rs41
from .decoders import lpc_opc
from .decoders import rpu_report
from .decoders import rachuts_report
from .decoders import rachuts_eeprom
from .registry import register, DecodeContext


@register("RATSREPORT")
def _rats_report(ctx: DecodeContext) -> None:
    if (ctx.show_payload or ctx.headers) and not ctx.has_payload:
        print("Binary payload not found for RATSREPORT, can't read headers or data")
        return
    if ctx.has_payload:
        # A records-less RATSREPORT can't emit the CSV header (the ECU columns
        # depend on a record); report back so the dispatcher doesn't treat it
        # as the first file that owns the header.
        ctx.header_emitted = rats_report.decode_payload(
            ctx.tm_filename, ctx.headers, ctx.show_payload,
            ctx.first_file, ctx.csv, ctx.float_format)


@register("RATSTCACK", "RATSTEXT")
def _rats_tcack(ctx: DecodeContext) -> None:
    if ctx.show_payload:
        rats_tcack.decode_payload(ctx.tm_filename, ctx.headers, ctx.show_payload,
                                  ctx.first_file, ctx.csv)


@register("RATSEEPROM")
def _rats_eeprom(ctx: DecodeContext) -> None:
    if ctx.show_payload:
        if not ctx.has_payload:
            return
        rats_eeprom.decode_payload(ctx.tm_filename, ctx.headers, ctx.show_payload,
                                   ctx.first_file, ctx.csv, ctx.float_format)


@register("MCBEEPROM")
def _mcb_eeprom(ctx: DecodeContext) -> None:
    if ctx.show_payload:
        if not ctx.has_payload:
            return
        mcb_eeprom.decode_payload(ctx.tm_filename, ctx.headers, ctx.show_payload,
                                  ctx.first_file, ctx.csv, ctx.float_format)


@register("RACHUTSEEPROM")
def _rachuts_eeprom(ctx: DecodeContext) -> None:
    if ctx.show_payload:
        if not ctx.has_payload:
            return
        rachuts_eeprom.decode_payload(ctx.tm_filename, ctx.headers, ctx.show_payload,
                                      ctx.first_file, ctx.csv, ctx.float_format)


@register("LPCRS41")
def _lpc_rs41(ctx: DecodeContext) -> None:
    ctx.tm_file.close()  # close so RS41msg can reopen the file by name
    if ctx.show_payload:
        if not ctx.has_payload:
            return
        lpc_rs41.decode_payload(ctx.tm_filename, ctx.headers, ctx.show_payload,
                                ctx.first_file, ctx.csv, ctx.float_format)


@register("LPCOPC")
def _lpc_opc(ctx: DecodeContext) -> None:
    if ctx.show_payload:
        if not ctx.has_payload:
            return
        lpc_opc.decode_payload(ctx.tm_filename, ctx.headers, ctx.show_payload,
                               ctx.first_file, ctx.csv, ctx.float_format)


@register("LPCTEXT")
def _lpc_text(ctx: DecodeContext) -> None:
    # LPC status/text TMs (e.g. "Unknown TC received") carry no binary
    # payload; nothing to decode.
    return


@register("MCBREPORT")
def _mcb_report(ctx: DecodeContext) -> None:
    if ctx.first_file and ctx.csv:
        print(mcb_report.csv_header())
    if ctx.show_payload:
        if not ctx.has_payload:
            return
        mcb_report.decode_payload(ctx.tm_filename, ctx.csv, ctx.float_format)


@register("RPUREPORT")
def _rpu_report(ctx: DecodeContext) -> None:
    if ctx.first_file and ctx.csv:
        print(rpu_report.csv_header())
    if ctx.show_payload:
        if not ctx.has_payload:
            return
        # The start reference (epoch, lat, lon) is carried in the payload's
        # block header; the profile number is in StateMess2.
        profile = rpu_report.parse_profile(ctx.xml_dict['TM'].get('StateMess2'))
        rpu_report.decode_payload(ctx.tm_filename, ctx.csv, ctx.float_format, profile)


@register("RACHUTSREPORT")
def _rachuts_report(ctx: DecodeContext) -> None:
    if ctx.show_payload or ctx.headers:
        if not ctx.has_payload:
            print("Binary payload not found for RACHUTSREPORT, can't read headers or data")
            return
        rachuts_report.decode_payload(ctx.tm_filename, ctx.headers, ctx.show_payload,
                                      ctx.first_file, ctx.csv, ctx.float_format)
