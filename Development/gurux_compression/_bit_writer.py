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
"""Write unaligned bit blocks to a caller-owned binary stream."""

from ._stream_io import write_all


class _BitWriter:
    """Carry partial bytes between blocks and align only at the final FLUSH."""

    def __init__(self, target):
        """Initialize a writer retaining at most seven bits between writes."""
        self._target = target
        self._buffer = 0
        self._available = 0

    def write(self, bits) -> None:
        """Append valid bits without introducing padding between blocks."""
        output = bytearray()
        position = 0
        while position < bits.size:
            count = min(8, bits.size - position)
            self._buffer |= bits.get(position, count) << self._available
            self._available += count
            position += count
            if self._available >= 8:
                output.append(self._buffer & 255)
                self._buffer >>= 8
                self._available -= 8
        write_all(self._target, output)

    def align(self) -> None:
        """Write a final partial byte padded with zeros, leaving the stream open."""
        if self._available:
            write_all(self._target, bytes((self._buffer,)))
            self._buffer = self._available = 0
