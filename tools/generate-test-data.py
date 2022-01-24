#!/usr/bin/env python

import argparse
import itertools
import os
import random
import struct

WRITE_CHUNK_SIZE = 4096


argument_parser = argparse.ArgumentParser()
argument_parser.add_argument("target_directory", default=".")
argument_parser.add_argument(
    "--lower-boundary-power",
    default=10,
    metavar="I",
    type=int,
    help="Generated file sizes start with 2^X",
)
argument_parser.add_argument(
    "--upper-boundary-power",
    default=20,
    metavar="I",
    type=int,
    help="Generated file sizes start with 2^J",
)
argument_parser.add_argument(
    "--random-seed",
    default=4,
    type=int,
    help="Seed for the random generator. Defaults to 4. Chosen by fair dice roll."
    " Guaranteed to be random. https://xkcd.com/221/",
)
args = argument_parser.parse_args()


def random_bytes(n: int) -> bytes:
    return (
        b"".join(
            map(
                struct.Struct("!Q").pack,
                map(random.getrandbits, itertools.repeat(64, (n + 7) // 8)),
            )
        )
    )[:n]


# method found at https://stackoverflow.com/questions/1094841/get-human-readable-version-of-file-size
def sizeof_fmt(num: float, suffix: str = "B") -> str:
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            if float(num).is_integer():
                return "%d%s%s" % (num, unit, suffix)
            else:
                return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


random.seed(args.random_seed)

for p in range(args.lower_boundary_power, args.upper_boundary_power + 1):
    size = 2 ** p
    size_human_readable = sizeof_fmt(size)
    filename = os.path.join(args.target_directory, "bfebench-test-%s.bin" % size_human_readable)

    print("Generating %s with size of %d bytes" % (filename, size))
    with open(filename, "wb") as fp:
        remaining = size
        while remaining > 0:
            chunk = random_bytes(min(WRITE_CHUNK_SIZE, remaining))
            fp.write(chunk)
            remaining -= len(chunk)
