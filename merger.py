#!/usr/bin/env python3
"""
Merge daily CSV files named like "de-gtfsde-TripUpdate-2026-09-30.csv"
(2026-09-30 through 2026-11-10) into a single CSV file.

Each daily file is ~130 MB (~550k rows), so the merged file will be several GB.
Files are copied as raw bytes (header skipped after the first file), which is
fast, uses almost no memory, and keeps the original quoting exactly as-is.
"""

import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

# ---------------- Configuration ----------------
INPUT_DIR = Path(".")                       # folder containing the daily CSVs
FILE_PATTERN = "de-gtfsde-TripUpdate-{d}.csv"
START_DATE = date(2026, 9, 30)
END_DATE = date(2026, 11, 10)
OUTPUT_FILE = Path("de-gtfsde-TripUpdate-merged.csv")
# -----------------------------------------------


def daterange(start: date, end: date):
    for i in range((end - start).days + 1):
        yield start + timedelta(days=i)


def main() -> int:
    header = None
    files_merged = 0
    missing = []

    with open(OUTPUT_FILE, "wb") as out_f:
        for d in daterange(START_DATE, END_DATE):
            day = d.isoformat()
            path = INPUT_DIR / FILE_PATTERN.format(d=day)

            if not path.exists():
                missing.append(day)
                continue

            with open(path, "rb") as in_f:
                file_header = in_f.readline()
                if not file_header:
                    print(f"Warning: {path.name} is empty, skipping.")
                    continue

                if header is None:
                    header = file_header
                    out_f.write(header)
                elif file_header.rstrip(b"\r\n") != header.rstrip(b"\r\n"):
                    print(f"Error: header in {path.name} differs from the first file.",
                          file=sys.stderr)
                    return 1

                # Copy everything after the header in large chunks
                shutil.copyfileobj(in_f, out_f, length=16 * 1024 * 1024)

            # Make sure the next file's first row starts on a new line
            if out_f.tell() > 0:
                with open(OUTPUT_FILE, "rb") as check:
                    check.seek(-1, 2)
                    if check.read(1) != b"\n":
                        out_f.write(b"\n")

            files_merged += 1
            print(f"Merged {path.name}")

    print(f"\nDone: {files_merged} files merged -> {OUTPUT_FILE}")
    if missing:
        print(f"Missing files for {len(missing)} date(s): {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())