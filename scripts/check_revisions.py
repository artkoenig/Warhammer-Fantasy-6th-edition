#!/usr/bin/env python3
"""Revision gate: every changed .cat/.gst file must carry a strictly higher
`revision="N"` attribute than the base ref. Files unchanged between the two
refs are ignored.

Usage:
    check_revisions.py <base-ref> [head-ref]

If head-ref is omitted, the working tree (including staged and unstaged
changes) is checked instead of a commit.
"""
import re
import subprocess
import sys

REVISION_RE = re.compile(r'(?<!System)\brevision="(\d+)"')


def git(*args):
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout


def changed_datafiles(base_ref, head_ref):
    diff_args = ["diff", "--name-only", "--diff-filter=d", base_ref]
    if head_ref is not None:
        diff_args.append(head_ref)
    paths = git(*diff_args).splitlines()
    return [p for p in paths if p.endswith(".cat") or p.endswith(".gst")]


def revision_at(ref, path):
    if ref is None:
        with open(path, "r", encoding="utf-8") as fh:
            head = fh.read(2000)
    else:
        try:
            head = git("show", f"{ref}:{path}")[:2000]
        except subprocess.CalledProcessError:
            return None  # file didn't exist at this ref (newly added)
    match = REVISION_RE.search(head)
    return int(match.group(1)) if match else None


def main():
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        return 2

    base_ref = sys.argv[1]
    head_ref = sys.argv[2] if len(sys.argv) == 3 else None

    files = changed_datafiles(base_ref, head_ref)
    if not files:
        print("No changed .cat/.gst files — nothing to check.")
        return 0

    failed = []
    for path in files:
        base_rev = revision_at(base_ref, path)
        head_rev = revision_at(head_ref, path)

        if base_rev is None:
            print(f"SKIP  {path} (new file, no base revision to compare)")
            continue
        if head_rev is None:
            print(f"FAIL  {path}: no revision=\"N\" attribute found")
            failed.append(path)
            continue
        if head_rev > base_rev:
            print(f"OK    {path}: revision {base_rev} -> {head_rev}")
        else:
            print(f"FAIL  {path}: revision not bumped ({base_rev} -> {head_rev})")
            failed.append(path)

    if failed:
        print(f"\n{len(failed)} file(s) changed without a revision bump:")
        for path in failed:
            print(f"  - {path}")
        return 1

    print(f"\nAll {len(files)} changed datafile(s) carry a bumped revision.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
