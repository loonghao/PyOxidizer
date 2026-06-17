#!/usr/bin/env python3
"""Generate default_python_distributions.rs from python-build-standalone release.

Usage: python scripts/gen_distributions.py --tag 20260602
Requires: gh CLI authenticated
"""

import argparse
import hashlib
import json
import subprocess
import sys
import urllib.parse
import urllib.request


def build_download_url(tag, name):
    """Build the download URL for a release asset."""
    encoded = urllib.parse.quote(name, safe='')
    return f"https://github.com/indygreg/python-build-standalone/releases/download/{tag}/{encoded}"


def run_gh(*args):
    result = subprocess.run(["gh", *args], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"gh error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def download_and_hash(url):
    """Download a file and compute its SHA256."""
    with urllib.request.urlopen(url) as r:
        h = hashlib.sha256()
        while True:
            chunk = r.read(32768)
            if not chunk:
                break
            h.update(chunk)
        return h.hexdigest()


def parse_asset_name(name):
    """Parse a python-build-standalone asset name.

    Returns (python_version, major_minor, target_triple, flavor) or None.
    """
    if not name.startswith("cpython-") or not name.endswith("-full.tar.zst"):
        return None

    # Remove prefix and suffix
    core = name[len("cpython-"):-len("-full.tar.zst")]

    # Split by '-'
    parts = core.split("-")

    # First part is version+tag
    version_tag = parts[0]
    python_version, _ = version_tag.split("+", 1)
    major_minor = python_version.rsplit(".", 1)[0]

    # Remaining parts are the target triple + flavor
    remaining = parts[1:]

    # Known target triple endings (from right to left)
    # Order matters: longer matches first
    ENDINGS = [
        "unknown-linux-gnueabihf",
        "unknown-linux-gnueabi",
        "unknown-linux-gnu",
        "unknown-linux-musl",
        "apple-darwin",
        "pc-windows-msvc",
    ]

    # Find where the target triple ends and flavor begins
    joined = "-".join(remaining)
    # Prepend a leading '-' to ensure we match complete segments
    joined_delim = "-" + joined

    for ending in ENDINGS:
        # Search for "-<ending>-" or "-<ending>" at end
        search = "-" + ending
        idx = joined_delim.find(search)
        if idx >= 0:
            # Everything up to and including the ending is the target triple
            # joined_delim has a leading '-', so adjust
            target_end = idx + len(search) - 1  # -1 for the leading '-'
            target_triple = joined[:target_end]
            flavor = joined[target_end:].lstrip("-")
            return python_version, major_minor, target_triple, flavor

    return None


def should_include(major_minor, target_triple, flavor):
    """Determine if this distribution should be included."""
    if target_triple not in SUPPORTED_TRIPLES:
        return False
    if supported_flavor_for_target(target_triple, flavor) is None:
        return False
    return True


def supports_ext_modules(target_triple):
    """Determine if this distribution supports prebuilt extension modules."""
    return "musl" not in target_triple


def supported_flavor_for_target(target_triple, flavor):
    """Return the preferred flavor for a given target triple, or None to skip."""
    # Preferred flavors per platform category
    if "linux-gnu" in target_triple:
        return "pgo+lto" if flavor == "pgo+lto" else None
    if "linux-musl" in target_triple:
        return "noopt" if flavor == "noopt" else None
    if "windows-msvc" in target_triple:
        return "pgo" if flavor == "pgo" else None
    if "apple-darwin" in target_triple:
        return "pgo+lto" if flavor == "pgo+lto" else None
    return None


# Supported target triples (most common ones)
SUPPORTED_TRIPLES = {
    # Linux glibc
    "aarch64-unknown-linux-gnu",
    "x86_64-unknown-linux-gnu",
    "x86_64_v2-unknown-linux-gnu",
    "x86_64_v3-unknown-linux-gnu",
    # Linux musl
    "x86_64-unknown-linux-musl",
    "x86_64_v2-unknown-linux-musl",
    "x86_64_v3-unknown-linux-musl",
    # Windows
    "i686-pc-windows-msvc",
    "x86_64-pc-windows-msvc",
    # macOS
    "aarch64-apple-darwin",
    "x86_64-apple-darwin",
}


ENTRY_TEMPLATE = """        PythonDistributionRecord {{
            python_major_minor_version: "{major_minor}".to_string(),
            location: PythonDistributionLocation::Url {{
                url: "{url}".to_string(),
                sha256: "{sha256}".to_string(),
            }},
            target_triple: "{target_triple}".to_string(),
            supports_prebuilt_extension_modules: {supports_prebuilt},
        }},"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", help="python-build-standalone release tag", required=True)
    parser.add_argument("--no-download", action="store_true",
                        help="Skip downloading files for SHA256 (use SHA256SUMS instead)")
    args = parser.parse_args()

    # Get asset list from GitHub
    print("Fetching asset list...", file=sys.stderr)
    assets_json = run_gh("release", "view", args.tag,
                         "-R", "indygreg/python-build-standalone",
                         "--json", "assets",
                         "--jq", '[.assets[] | {name}]')
    assets = json.loads(assets_json)

    # Filter to full distribution assets
    dist_assets = [a for a in assets
                   if a["name"].startswith("cpython-")
                   and a["name"].endswith("-full.tar.zst")]

    print(f"Found {len(dist_assets)} full distribution assets", file=sys.stderr)

    # Download SHA256SUMS
    print("Fetching SHA256SUMS...", file=sys.stderr)
    checksums_raw = run_gh("release", "download", args.tag,
                           "-R", "indygreg/python-build-standalone",
                           "-p", "SHA256SUMS",
                           "-O", "-")
    # Parse: "SHA256  filename"
    checksums = {}
    for line in checksums_raw.strip().split("\n"):
        if not line.strip():
            continue
        # Format: sha256  filename  OR  sha256 *filename
        parts = line.strip().split(None, 1)
        if len(parts) == 2:
            sha256, filename = parts
            filename = filename.lstrip("*").strip()
            checksums[filename] = sha256

    print(f"Loaded {len(checksums)} checksums", file=sys.stderr)

    # Parse and categorize
    records = {}  # key: (major_minor, target_triple, flavor) -> record

    for asset in dist_assets:
        result = parse_asset_name(asset["name"])
        if result is None:
            print(f"  SKIP (parse fail): {asset['name']}", file=sys.stderr)
            continue

        python_version, major_minor, target_triple, flavor = result

        if not should_include(major_minor, target_triple, flavor):
            continue

        # Get SHA256
        filename = asset["name"]
        sha256 = checksums.get(filename, "")
        if not sha256:
            # Try to download and compute
            if not args.no_download:
                print(f"  Downloading {filename} for SHA256...", file=sys.stderr)
                url = build_download_url(args.tag, filename)
                sha256 = download_and_hash(url)
            else:
                print(f"  WARNING: No SHA256 for {filename}", file=sys.stderr)
                continue

        records[(major_minor, target_triple, flavor)] = {
            "major_minor": major_minor,
            "target_triple": target_triple,
            "url": build_download_url(args.tag, filename),
            "sha256": sha256,
            "supports_prebuilt": "true" if supports_ext_modules(target_triple) else "false",
        }

    print(f"Parsed {len(records)} valid distribution records", file=sys.stderr)

    # Generate Rust code
    print("// This Source Code Form is subject to the terms of the Mozilla Public")
    print("// License, v. 2.0. If a copy of the MPL was not distributed with this")
    print("// file, You can obtain one at https://mozilla.org/MPL/2.0/.")
    print()
    print("// THIS FILE IS AUTOGENERATED. DO NOT EDIT MANUALLY.")
    print()
    print("//! Default Python distributions.")
    print()
    print("use crate::py_packaging::distribution::{")
    print("    PythonDistributionLocation, PythonDistributionRecord,")
    print("};")
    print("use crate::python_distributions::PythonDistributionCollection;")
    print("use once_cell::sync::Lazy;")
    print()
    print("pub static PYTHON_DISTRIBUTIONS: Lazy<PythonDistributionCollection> = Lazy::new(|| {")
    print("    let dists = vec![")

    # Define the order we want
    categories = [
        ("// Linux glibc linked.", ["linux-gnu"]),
        ("// Linux musl.", ["linux-musl"]),
        ("// Windows.", ["windows-msvc"]),
        ("// macOS.", ["apple-darwin"]),
    ]

    versions = ["3.10", "3.11", "3.12", "3.13"]

    for comment, platform_suffixes in categories:
        print(f"        {comment}")

        for version in versions:
            for key, rec in sorted(records.items()):
                if (key[0] == version and
                    any(key[1].endswith(suffix) for suffix in platform_suffixes)):
                    print(ENTRY_TEMPLATE.format(**rec))
        print()

    print("    ];")
    print()
    print("    PythonDistributionCollection { dists }")
    print("});")


if __name__ == "__main__":
    main()
