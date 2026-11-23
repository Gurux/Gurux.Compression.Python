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
"""Validated V.44 limits, copied when a codec is constructed."""

from copy import copy
from dataclasses import dataclass
from gettext import gettext as _

from .enums import MaximumStringLength


@dataclass
class V44Options:
    """Configure a codec before construction; later changes affect new codecs only.

    Attributes:
        default_codeword_size: Initial codeword width, 6 through 16 bits.
        default_ordinal_size: Initial literal width, 7 or 8 bits.
        max_codewords: Exclusive codeword limit, including four control codes.
        maximum_string_length: One of the four negotiated V.44 string modes.
        history_limit: Maximum history bytes between REINIT controls, at least 512.
        hex: Force hexadecimal formatting of diagnostic values.
    """

    default_codeword_size: int = 6
    default_ordinal_size: int = 7
    max_codewords: int = 1024
    maximum_string_length: MaximumStringLength = MaximumStringLength.VALUE_255
    history_limit: int = 3072
    hex: bool = False

    def validate(self) -> None:
        """Raise ValueError for unsupported types, bit widths or protocol limits."""
        for name, minimum, maximum in (
            ("default_codeword_size", 6, 16),
            ("default_ordinal_size", 7, 8),
            ("max_codewords", 256, 65535),
            ("history_limit", 512, 2147483647),
        ):
            value = getattr(self, name)
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not minimum <= value <= maximum
            ):
                raise ValueError(
                    _(
                        "{name} must be an integer between {minimum} and {maximum}."
                    ).format(name=name, minimum=minimum, maximum=maximum)
                )
        if not isinstance(
            self.maximum_string_length, int
        ) or self.maximum_string_length not in tuple(MaximumStringLength):
            raise ValueError(_("Unsupported maximum string length."))
        if not isinstance(self.hex, bool):
            raise ValueError(_("hex must be a boolean."))

    def _snapshot(self):
        """Validate and return an independent options copy for one codec."""
        self.validate()
        return copy(self)
