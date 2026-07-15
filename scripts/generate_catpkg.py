#!/usr/bin/env python3
"""Regenerate catpkg.json (BSData catpkg schema) from the .cat/.gst files in
the repository root.

Schema: https://raw.githubusercontent.com/BSData/schemas/master/src/catpkg.schema.json
"""
import json
import os
import re
import urllib.parse

REPO_OWNER = "artkoenig"
REPO_NAME = "Warhammer-Fantasy-6th-edition"
REPO_BRANCH = "master"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{REPO_BRANCH}"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ID_RE = re.compile(r'\bid="([^"]+)"')
NAME_RE = re.compile(r'\bname="([^"]+)"')
REVISION_RE = re.compile(r'(?<!System)\brevision="(\d+)"')


def datafile_meta(path):
    with open(path, "r", encoding="utf-8") as fh:
        head = fh.read(2000)
    return {
        "id": ID_RE.search(head).group(1),
        "name": NAME_RE.search(head).group(1),
        "revision": int(REVISION_RE.search(head).group(1)),
    }


def build_file_entry(filename):
    path = os.path.join(ROOT, filename)
    meta = datafile_meta(path)
    file_type = "gamesystem" if filename.endswith(".gst") else "catalogue"
    return {
        "id": meta["id"],
        "name": meta["name"],
        "type": file_type,
        "revision": meta["revision"],
        "fileUrl": f"{RAW_BASE}/{urllib.parse.quote(filename)}",
    }


def main():
    filenames = sorted(
        f for f in os.listdir(ROOT) if f.endswith(".cat") or f.endswith(".gst")
    )
    catpkg = {
        "$schema": "https://raw.githubusercontent.com/BSData/schemas/master/src/catpkg.schema.json",
        "name": "whfb6",
        "description": "Warhammer Fantasy Battle 6th Edition",
        "battleScribeVersion": "2.03",
        "repositoryUrl": f"{RAW_BASE}/catpkg.json",
        "githubUrl": f"https://github.com/{REPO_OWNER}/{REPO_NAME}",
        "repositoryFiles": [build_file_entry(f) for f in filenames],
    }

    out_path = os.path.join(ROOT, "catpkg.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(catpkg, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"Wrote {out_path} ({len(filenames)} datafiles).")


if __name__ == "__main__":
    main()
