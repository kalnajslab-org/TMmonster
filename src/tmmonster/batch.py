#!/usr/bin/env python3
"""
Catalog files by timestamp, group into fixed time windows, and run tmmonster on each group.

Expected filename timestamp format: ...YYYY-MM-DDTHH-MM-SS-mmm...
  e.g.  TM_2026-03-25T16-32-15-283.dat

Usage
-----
  # Scan a directory for .dat files, 30-minute windows:
  python3 tmmonster_catalog.py --dir /data/tm --ext .dat --window 30m

  # Explicit file list, 1-hour windows:
  python3 tmmonster_catalog.py --window 1h TM_2026-03-25T*.dat

  # Pass arguments to tmmonster after '--':
  python3 tmmonster_catalog.py --dir /data/tm --window 1h -- --flag value

  # Dry run (print commands, don't execute):
  python3 tmmonster_catalog.py --dir /data/tm --window 30m --dry-run
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# Timestamp parsing
# ---------------------------------------------------------------------------

# Format 1: YYYY-MM-DDTHH-MM-SS-mmm  e.g. TM_2026-03-25T16-32-15-283
_TIMESTAMP_RE1 = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{3})")

# Format 2: DD-Mon-YY_HH-MM-SS  e.g. TM_04-Mar-26_14-15-21
_TIMESTAMP_RE2 = re.compile(r"(\d{2}-[A-Za-z]{3}-\d{2}_\d{2}-\d{2}-\d{2})")


def parse_file_timestamp(filename: str) -> datetime | None:
    """Extract a datetime from a filename, supporting two formats:
      - YYYY-MM-DDTHH-MM-SS-mmm  (e.g. TM_2026-03-25T16-32-15-283)
      - DD-Mon-YY_HH-MM-SS       (e.g. TM_04-Mar-26_14-15-21)
    """
    m = _TIMESTAMP_RE1.search(filename)
    if m:
        ts_str = m.group(1)                        # e.g. 2026-03-25T16-32-15-283
        main, ms = ts_str.rsplit("-", maxsplit=1)   # split off milliseconds
        dt = datetime.strptime(main, "%Y-%m-%dT%H-%M-%S")
        return dt.replace(microsecond=int(ms) * 1000)

    m = _TIMESTAMP_RE2.search(filename)
    if m:
        return datetime.strptime(m.group(1), "%d-%b-%y_%H-%M-%S")

    return None


# ---------------------------------------------------------------------------
# Window duration parsing
# ---------------------------------------------------------------------------

def parse_window(value: str) -> timedelta:
    """Parse a duration string: 1h, 30m, 90s, 1h30m, etc."""
    m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", value.strip())
    if not m or not any(m.groups()):
        raise argparse.ArgumentTypeError(
            f"Invalid window {value!r}. Use e.g. 1h, 30m, 1h30m, 90s"
        )
    hours   = int(m.group(1) or 0)
    minutes = int(m.group(2) or 0)
    seconds = int(m.group(3) or 0)
    td = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    if td.total_seconds() == 0:
        raise argparse.ArgumentTypeError("Window duration must be > 0")
    return td


# ---------------------------------------------------------------------------
# File collection
# ---------------------------------------------------------------------------

def collect_files(args: argparse.Namespace) -> list[Path]:
    if args.files:
        paths = [Path(f) for f in args.files]
        missing = [p for p in paths if not p.exists()]
        if missing:
            sys.exit("Error: file(s) not found:\n" + "\n".join(f"  {p}" for p in missing))
        return paths

    directory = Path(args.dir)
    if not directory.is_dir():
        sys.exit(f"Error: not a directory: {directory}")
    ext = args.ext if args.ext.startswith(".") else f".{args.ext}"
    return sorted(directory.glob(f"*{ext}"))


# ---------------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------------

def group_files(
    files: list[Path], window: timedelta
) -> list[tuple[datetime, datetime, list[Path]]]:
    """Return [(window_start, window_end, [files]), ...], sorted by time, empty windows omitted."""
    stamped: list[tuple[datetime, Path]] = []
    for f in files:
        ts = parse_file_timestamp(f.name)
        if ts is None:
            print(f"Warning: no timestamp found in filename, skipping: {f.name}", file=sys.stderr)
        else:
            stamped.append((ts, f))

    if not stamped:
        return []

    stamped.sort(key=lambda x: x[0])
    t_start = stamped[0][0]
    t_end   = stamped[-1][0]

    groups: list[tuple[datetime, datetime, list[Path]]] = []
    win_start = t_start
    while win_start <= t_end:
        win_end = win_start + window
        bucket  = [f for ts, f in stamped if win_start <= ts < win_end]
        if bucket:
            groups.append((win_start, win_end, bucket))
        win_start = win_end

    return groups


# ---------------------------------------------------------------------------
# tmmonster execution
# ---------------------------------------------------------------------------

def run_tmmonster(
    window_start: datetime,
    files: list[Path],
    tmmonster_args: list[str],
    dry_run: bool,
    verbose: bool = False,
    out_ext: str = ".csv",
) -> None:
    cmd = ["tmmonster"] + tmmonster_args + [str(f) for f in files]
    log_path = Path(f"tmdata_{window_start.strftime('%Y-%m-%dT%H-%M-%S')}{out_ext}")
    if verbose or dry_run:
        print("$", " ".join(cmd))
        print(f"  → {log_path}")
    if not dry_run:
        with log_path.open("w") as log_file:
            result = subprocess.run(cmd, stdout=log_file, stderr=log_file, check=False)
        if result.returncode != 0:
            print(
                f"Warning: tmmonster exited with code {result.returncode} "
                f"for window starting {window_start.isoformat()} (see {log_path})",
                file=sys.stderr,
            )


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Catalog files by timestamp, group into time windows, "
            "and run tmmonster on each group."
        ),
        epilog=(
            "Requires tmmonster to be installed and available on PATH.\n"
            "Install it with: pip install -e /path/to/TMmonster\n"
            "  or:            pip install tmmonster\n"
            "\n"
            "Append tmmonster arguments after '--', e.g.:\n"
            "  tmmonster-batch --dir /data --window 1h -- --csv --payload"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--dir", metavar="DIR",
        help="Directory to scan for files.",
    )
    source.add_argument(
        "files", nargs="*", metavar="FILE", default=[],
        help="Explicit list of files (alternative to --dir).",
    )
    parser.add_argument(
        "--ext", default=".dat", metavar="EXT",
        help="File extension filter when using --dir (default: .dat).",
    )
    parser.add_argument(
        "--window", required=True, type=parse_window, metavar="DURATION",
        help="Time window size, e.g. 1h, 30m, 1h30m, 90s.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print tmmonster commands without executing them.",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print each tmmonster command before running it.",
    )
    parser.add_argument(
        "--out-ext", default=".csv", metavar="EXT",
        help="Output file extension (default: .csv).",
    )
    return parser


def split_argv(argv: list[str]) -> tuple[list[str], list[str]]:
    """Split argv at '--' into (script args, tmmonster args)."""
    if "--" in argv:
        idx = argv.index("--")
        return argv[:idx], argv[idx + 1:]
    return argv, []


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    main_argv, tmmonster_args = split_argv(sys.argv[1:])
    parser = build_parser()
    args = parser.parse_args(main_argv)

    # Validate: --dir and positional files are mutually exclusive
    if args.dir and args.files:
        parser.error("Specify either --dir or a list of files, not both.")
    if not args.dir and not args.files:
        parser.error("Specify --dir DIR or provide files on the command line.")

    files = collect_files(args)
    if not files:
        sys.exit("No files found.")

    window_str = str(args.window)  # e.g. '1:00:00'
    groups = group_files(files, args.window)

    print(
        f"Found {len(files)} file(s) → {len(groups)} non-empty window(s) "
        f"of {args.window}"
    )
    if args.dry_run:
        print("(dry-run: tmmonster will not be executed)\n")

    for win_start, win_end, bucket in groups:
        label = f"{win_start.strftime('%Y-%m-%dT%H:%M:%S')} – {win_end.strftime('%Y-%m-%dT%H:%M:%S')}"
        print(f"\n[{label}]  {len(bucket)} file(s)")
        out_ext = args.out_ext if args.out_ext.startswith(".") else f".{args.out_ext}"
        run_tmmonster(win_start, bucket, tmmonster_args, args.dry_run, args.verbose, out_ext)


if __name__ == "__main__":
    main()
