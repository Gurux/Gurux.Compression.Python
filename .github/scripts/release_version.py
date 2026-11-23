# --------------------------------------------------------------------------
# Gurux Ltd
#
# Copyright (c) Gurux Ltd.
#
# This file is part of Gurux Device Framework.
#
# Commit: $Format:%H$
# Date:   $Format:%cI$
#
# This software is available under either of the following licenses:
#
# 1. GNU General Public License, version 2 only (GPL-2.0-only).
#    See the LICENSE file included with this distribution.
#
# 2. A commercial license granted by Gurux Ltd under a separate written
#    agreement. Use under this option requires a valid commercial license
#    and is governed by the terms of that agreement.
#
# If you have not obtained a commercial license from Gurux Ltd,
# use of this software is governed by GPL-2.0-only.
#
# Commercial licensing: https://www.gurux.fi/
#
# SPDX-License-Identifier: GPL-2.0-only OR LicenseRef-Gurux-Commercial
# --------------------------------------------------------------------------
"""Select a patch release from vX.Y.Z tags and update package metadata."""

import os
from pathlib import Path
import re
import subprocess
from typing import List


def git(*args: str) -> List[str]:
    """Run Git synchronously in the current directory and return output lines.

    Args:
        *args: Git subcommand and arguments, passed without a shell.

    Returns:
        Standard output split into lines, without line terminators.

    Raises:
        OSError: Git cannot be started.
        subprocess.CalledProcessError: Git returns a nonzero exit status.

    This developer helper inherits standard error and waits without a timeout.
    """
    return subprocess.check_output(["git", *args], text=True).splitlines()


def release_version() -> None:
    """Select a release from repository tags and write GitHub Actions outputs.

    Run from the repository root. Reuse a tag for GITHUB_SHA, or a matching
    HEAD tag, on retries; otherwise increment the highest patch version.
    Start at 1.0.1 when no release tags exist. Update Development/setup.py
    only when its version differs, append version and existing outputs to
    GITHUB_OUTPUT, and print a developer diagnostic. Return None.

    Raises:
        KeyError: GITHUB_OUTPUT is absent from the environment.
        ValueError: Metadata has no unique version field or disagrees with
            an existing HEAD tag that does not identify the source commit.
        OSError: Git cannot start or a metadata/output file cannot be accessed.
        subprocess.CalledProcessError: A Git command fails.

    Git calls block without a timeout. This function modifies shared metadata
    and output files; the caller must serialize releases. It neither creates
    tags nor publishes packages. Process interruption propagates normally.
    """
    pattern = re.compile(r"v(\d+)\.(\d+)\.(\d+)")
    tags = {
        tag: tuple(map(int, pattern.fullmatch(tag).groups()))
        for tag in git("tag", "--list", "v*")
        if pattern.fullmatch(tag)
    }
    head_tags = [tags[tag] for tag in git("tag", "--points-at", "HEAD") if tag in tags]
    source_sha = os.environ.get("GITHUB_SHA") or git("rev-parse", "HEAD")[0]
    source_tags = []
    for line in git("tag", "--list", "--format=%(refname:short) %(contents:subject)"):
        tag, _, message = line.partition(" ")
        if tag in tags and message == f"Source: {source_sha}":
            source_tags.append(tags[tag])
    current = source_tags or head_tags
    existing = bool(current)
    if existing:
        version = max(current)
    elif tags:
        major, minor, patch = max(tags.values())
        version = (major, minor, patch + 1)
    else:
        version = (1, 0, 1)
    value = ".".join(map(str, version))

    setup = Path("Development/setup.py")
    source = setup.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'(?m)^(\s*version=)"\d+\.\d+\.\d+"',
        lambda match: f'{match[1]}"{value}"',
        source,
    )
    if count != 1:
        raise ValueError("Expected exactly one version field in Development/setup.py")
    if head_tags and not source_tags and updated != source:
        raise ValueError("The HEAD release tag does not match the package version")
    if updated != source:
        setup.write_text(updated, encoding="utf-8")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"version={value}\nexisting={str(existing).lower()}\n")
    print(f"Release version: {value} (existing tag: {existing})")


if __name__ == "__main__":
    release_version()
