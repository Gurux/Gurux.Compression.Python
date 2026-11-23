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
"""Decoder dictionary metadata exported as detached diagnostic snapshots."""

from typing import Optional
from ._diagnostic_value import _DiagnosticValue


class V44DecoderEntry:
    """Describe a decoded string ending at a zero-based history position."""

    def __init__(
        self,
        codeword: int = 0,
        position: int = 0,
        length: int = 0,
        value: Optional[str] = None,
    ) -> None:
        """Initialize the codeword, final history position, length and trace value."""
        self.codeword = codeword
        self.position = position
        self.length = length
        self._diagnostic = _DiagnosticValue(value)

    @property
    def start_position(self) -> int:
        """Return the first history index occupied by this dictionary string."""
        return self.position - self.length + 1

    @property
    def value(self) -> Optional[str]:
        """Return the lazily formatted diagnostic bytes for this entry."""
        return self._diagnostic.value

    @value.setter
    def value(self, value: Optional[str]) -> None:
        """Replace diagnostic text without affecting the decoded string."""
        self._diagnostic.value = value

    def _snapshot(self):
        """Return a detached entry, materializing the diagnostic value."""
        return V44DecoderEntry(self.codeword, self.position, self.length, self.value)

    def __str__(self) -> str:
        """Format dictionary metadata for developer trace inspection."""
        return (
            f"{{Codeword:{self.codeword} Position:{self.position} "
            f"Length:{self.length} Value:{self.value}}}"
        )
