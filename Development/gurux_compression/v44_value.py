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
"""Format legacy dictionary snapshots as ASCII or hexadecimal text."""

from typing import Sequence, Union


def format_v44_value(
    data: Union[bytes, bytearray, memoryview, Sequence[int]],
    index: int,
    count: int,
    hex_: bool,
) -> str:
    """Return a formatted copy of the selected dictionary bytes.

    Args:
        data: Sliceable byte values accepted by the bytes constructor.
        index: Slice start; normal Python slicing rules apply.
        count: Number of bytes requested; the source may yield fewer bytes.
        hex_: Force uppercase hexadecimal output with a 0x prefix.

    Returns:
        ASCII text when all bytes are at most 0x7F and exclude NUL, LF and CR,
        unless hex_ is true. Otherwise return prefixed hexadecimal text.

    Raises:
        TypeError: The source cannot be sliced or converted to bytes.
        ValueError: A selected integer is outside the byte range.

    This synchronous helper does not modify the source. Concurrent mutations
    of a mutable source require caller synchronization.
    """
    chunk = bytes(data[index : index + count])
    ascii_value = not hex_
    if not hex_:
        for item in chunk:
            if item > 0x7F or item in (0, 10, 13):
                ascii_value = False
                break
    if ascii_value:
        return chunk.decode("utf-8")
    return "0x" + chunk.hex().upper()
