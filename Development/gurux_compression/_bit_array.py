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
"""Private compact LSB-first codec storage with explicit logical bit bounds."""

from gettext import gettext as _
from typing import Optional, Union


class _BitArray:
    """Store variable-width fields; reads never advance position automatically."""

    def __init__(self) -> None:
        """Create an empty bit buffer without preallocating backing storage."""
        self._size = 0
        self._position = 0
        self._data = bytearray()

    @property
    def capacity(self) -> int:
        """Return allocated capacity in bits, rounded to whole bytes."""
        return len(self._data) * 8

    @capacity.setter
    def capacity(self, value: int) -> None:
        """Resize storage; a smaller capacity truncates data and clamps position."""
        if value < 0:
            raise ValueError(_("Capacity cannot be negative."))
        self.size = min(self.size, value)
        count = (value + 7) // 8
        if count < len(self._data):
            del self._data[count:]
        else:
            self._data.extend(b"\x00" * (count - len(self._data)))

    @property
    def size(self) -> int:
        """Return the number of logically valid bits."""
        return self._size

    @size.setter
    def size(self, value: int) -> None:
        """Set logical size within capacity, clearing removed bits on shrink."""
        if value < 0 or value > self.capacity:
            raise ValueError(_("Size must be between zero and capacity."))
        if value < self._size:
            start = (value + 7) // 8
            if value % 8:
                self._data[value // 8] &= (1 << (value % 8)) - 1
            self._data[start:] = b"\x00" * (len(self._data) - start)
        self._size = value
        self._position = min(self._position, value)

    @property
    def position(self) -> int:
        """Return the caller-controlled read cursor in bits."""
        return self._position

    @position.setter
    def position(self, value: int) -> None:
        """Set the cursor within the logical data, or raise ValueError."""
        if value < 0 or value > self.size:
            raise ValueError(_("Position is outside the valid bit range."))
        self._position = value

    @property
    def available(self) -> int:
        """Return the number of valid bits following the read cursor."""
        return self.size - self.position

    def array(self) -> bytes:
        """Return detached used bytes, with zero padding in the last byte."""
        return bytes(self._data[: (self.size + 7) // 8])

    def get(self, index: int, count: Optional[int] = None) -> Union[bool, int]:
        """Read one bit or 1â€“32 bits without advancing position.

        Raise ValueError if the field extends beyond the logical data.
        """
        width = 1 if count is None else count
        if not 1 <= width <= 32 or index < 0 or index + width > self.size:
            raise ValueError(_("Bit read is outside the valid range."))
        first = index // 8
        end = (index + width + 7) // 8
        value = int.from_bytes(self._data[first:end], "little")
        value = (value >> (index % 8)) & ((1 << width) - 1)
        return bool(value) if count is None else value

    def _ensure_capacity(self, bits: int) -> None:
        """Grow geometrically when an appended field exceeds current capacity."""
        if bits > self.capacity:
            self.capacity = max(bits, 64, self.capacity * 2)

    def add(
        self,
        value: Union[str, bytes, bytearray, memoryview, int],
        count: Optional[int] = None,
    ) -> None:
        """Append binary text, bytes or the lowest 1â€“32 bits of an integer.

        Whitespace in binary text is ignored. Invalid characters, widths and
        unsupported input types raise ValueError or TypeError respectively.
        """
        if isinstance(value, str):
            for bit in value:
                if bit in "01":
                    self.add(int(bit), 1)
                elif not bit.isspace():
                    raise ValueError(_("Expected binary digits or whitespace."))
            return
        if isinstance(value, (bytes, bytearray, memoryview)):
            value = bytes(value)
            if self.size % 8 == 0:
                self._ensure_capacity(self.size + len(value) * 8)
                first = self.size // 8
                self._data[first : first + len(value)] = value
                self._size += len(value) * 8
            else:
                for item in value:
                    self.add(item, 8)
            return
        if not isinstance(value, int):
            raise TypeError(_("Expected bytes, binary text or an integer."))
        width = 1 if count is None else count
        if not 1 <= width <= 32:
            raise ValueError(_("Bit width must be between 1 and 32."))
        self._ensure_capacity(self.size + width)
        offset, first = self.size % 8, self.size // 8
        combined = (value & ((1 << width) - 1)) << offset
        combined |= self._data[first] & ((1 << offset) - 1)
        count_bytes = (offset + width + 7) // 8
        self._data[first : first + count_bytes] = combined.to_bytes(
            count_bytes, "little"
        )
        self._size += width

    def to_bit_string(self) -> str:
        """Return exactly the valid bits in transmission order, without padding."""
        return "".join("1" if self.get(index) else "0" for index in range(self.size))

    def to_string(self, hexadecimal: bool = False) -> str:
        """Format used bytes as uppercase hex or bits separated at byte boundaries."""
        if hexadecimal:
            return self.array().hex().upper()
        bits = self.to_bit_string()
        return " ".join(bits[index : index + 8] for index in range(0, len(bits), 8))

    def __str__(self) -> str:
        """Return binary text separated at byte boundaries."""
        return self.to_string()
