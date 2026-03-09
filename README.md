# TMmonster

This is an application for decoding StratoCore TeleMessages. It uses
the handy python `bitstruct` module.

`bitstruct` lets you extract arbitrary bit fields from a vector
of bytes. A format string defines the bit fields.

***The `_bits` format strings (see below) must exactly match the bitfield definitions in 
   RATSReportHeader_t and ECUReport_t.***

The binary payload of the RATSReport TM starts with a
`StratoRats::RATSReportHeader_t`, and then is followed by a list of
`ECUComm::ECUReport_t` records, straight from the ECU's mouth.

The `RATSReport` contains a bit of metadata. Espcially important fields are:

- `header_size_bytes`: (uint8_t) the number of bytes in the header, including
   this byte.
- `num_ecu_records`: The number of `ECUReport`records. It can be zero.

## Install and Run

### 1) Install as a Python package from GitHub and run

```sh
python3 -m pip install "git+https://github.com/kalnajslab-org/TMmonster.git"
TMmonster 
```

### 2) Install as a Python package from local repository as editable and run

```sh
python3 -m pip install -e .
TMmonster
```

### 3) Run from local repository without installing

```sh
python3 TMmonster.py
```

### 4) Uninstall TMmonster

```sh
python3 -m pip uninstall tmmonster
```

## Report Versions

`TMmonster` can decode TMs of varying versions.

Both `RATSReport` and `ECUReport` contain version numbers. The version must appear at the
same location (first four bits) for all reports. (Note that we are limited version values < 16).

This code is not as well engineered as it could be. The following variables
and functions must be modified whenever the version number `<n>` increases for:
- `RATSReport`
    - Add an entry to `rats_bits[<n>]`.
    - Add an entry to `rats_field_names[<n>]`.
    - Add a scaling function `rats_scaled_vars_v<n>`
- `ECUReport`
    - Add an entry to `ecu_bits[<n>]`.
    - Add an entry to `ecu_field_names[<n>]`.
    - Add a scaling function `ecu_scaled_vars_v<n>`

## View TM Errors

Sometimes one TM out of many may become corrupted, and you need a quick way to find out which one
is causing a problem. `TMmonster` raises an exception on decoding errors, prints a traceback, and 
proceeds. Since the exception is printed to stderr, you can use `tmmonster * --sum  --pay >/dev/null`
to find and print just the TMs with errors:

```bash
tmmonster * --sum  --pay >/dev/null                    
Error processing file /Users/charlie/Work/LASP/Strateole2/TestData/RATS/RATS_2026-03-08T14-04-11/TM/TM_2026-03-08T19-02-27.RATS.dat: index out of range
Exception origin: /Users/charlie/Work/LASP/Strateole2/Apps/TMmonster/src/tmmonster/RATSEEPROM.py:62
Python line: eeprom['paired_ecu'] = payload[19]
Traceback:
Traceback (most recent call last):
  File "/Users/charlie/Work/LASP/Strateole2/Apps/TMmonster/src/tmmonster/TMmonster.py", line 197, in main
    RATSEEPROM.decode_payload(payload, args.headers, args.payload, first_file, args.csv, args.float_format)
  File "/Users/charlie/Work/LASP/Strateole2/Apps/TMmonster/src/tmmonster/RATSEEPROM.py", line 62, in decode_payload
    eeprom['paired_ecu'] = payload[19]
IndexError: index out of range
```

## bitstruct

`bitstruct` would not install on my older iMac, failing with:
```sh
     ld: library 'System' not found
      clang: error: linker command failed with exit code 1 (use -v to see invocation)
      error: command '/usr/local/bin/clang' failed with exit code 1

```

To get it to install, I did the following:
- downgraded my Xcode to one that matched
  MacOS 13.7.4. I got it from https://xcodereleases.com.
```sh
export LDFLAGS=-L/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib
pip install bitstruct
```

It's not clear that I needed to downgrade `Xcode`
