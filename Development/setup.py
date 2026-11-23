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
"""Setuptools metadata for the Gurux V.44 compression package."""

from pathlib import Path
import setuptools

PROJECT_DIRECTORY = Path(__file__).resolve().parent
"""Directory containing package metadata, the README and license resources."""

setuptools.setup(
    name="gurux_compression",
    version="1.0.1",
    author="Gurux Ltd",
    author_email="gurux@gurux.fi",
    description="Gurux V.44 compression package.",
    long_description=(PROJECT_DIRECTORY / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/gurux/gurux.compression.python",
    packages=setuptools.find_packages(exclude=("tests", "tests.*")),
    python_requires=">=3.7",
    license_expression="GPL-2.0-only OR LicenseRef-Gurux-Commercial",
    license_files=["LICENSE", "LICENSES/LicenseRef-Gurux-Commercial"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Operating System :: OS Independent",
    ],
)
