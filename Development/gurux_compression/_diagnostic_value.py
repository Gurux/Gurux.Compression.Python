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
"""Lazy diagnostic formatting without retaining data after materialization."""

from typing import Optional


class _DiagnosticValue:
    """Retain a source range until its ASCII or hexadecimal value is requested."""

    __slots__ = ("_data", "_index", "_count", "_hex", "_value")

    def __init__(self, value: Optional[str] = None):
        """Initialize an already formatted value without retained source bytes."""
        self._data = None
        self._index = self._count = 0
        self._hex = False
        self._value = value

    def capture(self, data, index: int, count: int, hexadecimal: bool) -> None:
        """Retain a valid source range, replacing any previously cached value."""
        self._data = data
        self._index = index
        self._count = count
        self._hex = hexadecimal
        self._value = None

    @property
    def value(self) -> Optional[str]:
        """Format once, release the source reference and return the cached text."""
        if self._data is not None:
            chunk = self._data[self._index : self._index + self._count]
            ascii_value = not self._hex and all(
                item <= 127 and item not in (0, 10, 13) for item in chunk
            )
            self._value = (
                chunk.decode("ascii") if ascii_value else "0x" + chunk.hex().upper()
            )
            self._data = None
        return self._value

    @value.setter
    def value(self, value: Optional[str]) -> None:
        """Replace cached text and release any unformatted source reference."""
        self._value = value
        self._data = None
