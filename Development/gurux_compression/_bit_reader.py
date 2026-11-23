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
"""Strict LSB-first token reading from a binary stream."""

from gettext import gettext as _
from ._stream_io import read_bytes
from .invalid_data_error import InvalidDataError


class _BitReader:
    """Buffer input bytes and reject truncated tokens or nonzero FLUSH padding."""

    def __init__(self, source):
        """Initialize a stream reader with bounded byte and bit lookahead."""
        self._source = source
        self._data = b""
        self._index = 0
        self._buffer = 0
        self._available = 0
        self.position = 0

    def _read_byte(self):
        """Return the next byte, or None at end of the binary input stream."""
        if self._index == len(self._data):
            self._data = read_bytes(self._source, 8192)
            self._index = 0
            if not self._data:
                return None
        value = self._data[self._index]
        self._index += 1
        return value

    def peek(self):
        """Return the next bit without advancing, or None at end of input."""
        if not self._available:
            value = self._read_byte()
            if value is None:
                return None
            self._buffer = value
            self._available = 8
        return self._buffer & 1

    def read(self, count: int) -> int:
        """Consume 1–16 low-order bits; reject incomplete tokens."""
        if not 1 <= count <= 16:
            raise ValueError(_("Token width must be between 1 and 16."))
        while self._available < count:
            value = self._read_byte()
            if value is None:
                raise InvalidDataError(
                    _("Truncated token at bit {position}.").format(
                        position=self.position + self._available
                    )
                )
            self._buffer |= value << self._available
            self._available += 8
        value = self._buffer & ((1 << count) - 1)
        self._buffer >>= count
        self._available -= count
        self.position += count
        return value

    def align(self) -> None:
        """Consume zero padding through the next byte boundary, or reject it."""
        padding = (-self.position) % 8
        if padding and self.read(padding):
            raise InvalidDataError(_("FLUSH padding must contain only zero bits."))
