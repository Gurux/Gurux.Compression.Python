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
"""Enumerations describing V.44 operations and negotiated limits."""

from enum import IntEnum


class MaximumStringLength(IntEnum):
    """
    Predefined maximum string lengths.
    """

    VALUE_46 = 46
    """
    The maximum string length is 46 characters.
    """
    VALUE_78 = 78
    """
    The maximum string length is 78 characters.
    """
    VALUE_142 = 142
    """
    The maximum string length is 142 characters.
    """
    VALUE_255 = 255
    """
    The maximum string length is 255 characters.
    """
