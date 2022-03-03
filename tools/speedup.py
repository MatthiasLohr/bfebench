#!/usr/bin/env python


from argparse import ArgumentParser
from datetime import datetime, time


def main() -> None:
    argument_parser = ArgumentParser()
    argument_parser.add_argument("t1start", type=time.fromisoformat)
    argument_parser.add_argument("t1stop", type=time.fromisoformat)
    argument_parser.add_argument("t2start", type=time.fromisoformat)
    argument_parser.add_argument("t2stop", type=time.fromisoformat)
    args = argument_parser.parse_args()

    if args.t1start > args.t1stop:
        raise ValueError("t1 start higher than stop")

    if args.t2start > args.t2stop:
        raise ValueError("t2 start higher than stop")

    t1start_combined = datetime.combine(datetime.today(), args.t1start)
    t1stop_combined = datetime.combine(datetime.today(), args.t1stop)
    t2start_combined = datetime.combine(datetime.today(), args.t2start)
    t2stop_combined = datetime.combine(datetime.today(), args.t2stop)

    diff1 = t1stop_combined - t1start_combined
    diff2 = t2stop_combined - t2start_combined

    speedup = diff1.total_seconds() / diff2.total_seconds()

    print(f"Speedup: {speedup}")


if __name__ == "__main__":
    main()
