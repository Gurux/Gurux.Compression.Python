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
"""Encoder dictionary metadata exported as detached diagnostic snapshots."""

# Protocol state and detached snapshots intentionally span these fields/helpers.
# pylint: disable=too-many-instance-attributes

from ._diagnostic_value import _DiagnosticValue
from .enums import Operation


class V44Node:
    """Describe one encoder segment and its child/sibling codeword links.

    Positions and lengths refer to segments, excluding their implicit root byte.
    Mutating an exported node never changes the encoder dictionary.
    """

    def __init__(self, codeword: int = 0, position: int = 0, length: int = 0) -> None:
        """Initialize segment metadata with ORDINAL operation and no links."""
        self.codeword = codeword
        self.position = position
        self.length = length
        self.operation = Operation.ORDINAL
        self.down_index = 0
        self.side_index = 0
        self._diagnostic = _DiagnosticValue("")

    @property
    def value(self) -> str:
        """Return the captured ASCII or hexadecimal diagnostic value."""
        return self._diagnostic.value

    @value.setter
    def value(self, value: str) -> None:
        """Replace diagnostic text without modifying dictionary metadata."""
        self._diagnostic.value = value

    def _snapshot(self):
        """Return independent metadata and materialize retained source bytes."""
        node = V44Node(self.codeword, self.position, self.length)
        node.operation = self.operation
        node.down_index = self.down_index
        node.side_index = self.side_index
        node.value = self.value
        return node

    def __str__(self) -> str:
        """Format segment metadata for developer trace inspection."""
        if self.length == 0:
            return f"'{self.value}' "
        text = (
            f"Codeword:{self.codeword} {self.value} "
            f"Position:{self.position} Length: {self.length}"
        )
        if self.down_index:
            text += f" DownIndex: {self.down_index}"
        if self.side_index:
            text += f" SideIndex: {self.side_index}"
        return text
