import argparse
from .RatsTM import main

def cli():
    parser = argparse.ArgumentParser(description="Decode RATS TM binary files.")
    parser.add_argument("tm_file", nargs='+', help="Path(s) to the TM file(s)")
    parser.add_argument("--header-only", action="store_true", help="Print only the RATSREPORT header")
    args = parser.parse_args()
    main(args)

if __name__ == "__main__":
    cli()
