#!/usr/bin/env python

from argparse import ArgumentParser
from datetime import datetime, time, timedelta

INTERVALS = {"second": 1, "minute": 60, "hour": 3600}


def main() -> None:
    argument_parser = ArgumentParser()
    argument_parser.add_argument("starttime", type=time.fromisoformat)
    argument_parser.add_argument("stoptime", type=time.fromisoformat)
    argument_parser.add_argument("--iterations", default=100, type=int)
    argument_parser.add_argument("--interval", choices=INTERVALS.keys(), default="minute")

    args = argument_parser.parse_args()

    start_combined = datetime.combine(datetime.today(), args.starttime)
    stop_combined = datetime.combine(datetime.today(), args.stoptime)

    diff_total = stop_combined - start_combined
    diff_single = timedelta(seconds=diff_total.total_seconds() / args.iterations)

    print(f"Total Time: {str(diff_total)}")
    print(f"Avg. Time: {str(diff_single)}")
    print(f"Avg. Perf.: (1/{args.interval}): {INTERVALS[args.interval]/diff_single.total_seconds()}")


if __name__ == "__main__":
    main()
