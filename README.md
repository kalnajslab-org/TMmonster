# RatsTM

This is a prototype app for decoding RATSReport TeleMessages. It uses
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

## Running

```sh
python3 RatsTM.py <file>
```

## Report Versions

`RatsTM` can decode TMs of varying versions.

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
