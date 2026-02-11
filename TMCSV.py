def print_list_csv(data, float_fmt):
    """
    Prints a list in CSV format.
    If a value is a float, it is formatted using float_fmt.
    """
    fmt = f'{{:{float_fmt}}}'  # Create a format string for floats
    row = []
    for v in data:
        if isinstance(v, float) and float_fmt:
            row.append(fmt.format(v))
        else:
            row.append(str(v))
    print(",".join(row))