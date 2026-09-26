"""Persist complete regression evidence without treating skipped tests as passes."""

from __future__ import annotations
import argparse
import datetime
import io
import platform
from pathlib import Path
import sys
import unittest
from .support import ROOT
from .evidence import source_fingerprint
from tool.build_support.storage import fingerprint, json_text, replace_checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    before = source_fingerprint()
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / "tests/build_system"), top_level_dir=str(ROOT)
    )
    text = io.StringIO()
    result = unittest.TextTestRunner(stream=text, verbosity=2).run(suite)
    output = text.getvalue()
    print(output, end="")
    after = source_fingerprint()
    stable = before == after
    report = {
        "schema_version": 1,
        "date": datetime.date.today().isoformat(),
        "host": platform.platform(),
        "python": sys.version,
        "tests": result.testsRun,
        "passed": result.wasSuccessful() and stable,
        "source_before": before,
        "source_after": after,
        "source_unchanged": stable,
        "failures": [{"test": str(test), "detail": detail} for test, detail in result.failures],
        "errors": [{"test": str(test), "detail": detail} for test, detail in result.errors],
        "skipped": [{"test": str(test), "reason": reason} for test, reason in result.skipped],
    }
    replace_checked(args.report, json_text(report), expected=fingerprint(args.report))
    log = args.report.with_suffix(".log")
    replace_checked(log, output, expected=fingerprint(log))
    return 0 if result.wasSuccessful() and stable else 1


if __name__ == "__main__":
    raise SystemExit(main())
