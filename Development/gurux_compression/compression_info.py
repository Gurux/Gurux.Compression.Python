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
"""Legacy compression record retained at its original import path."""

from dataclasses import dataclass


@dataclass
class GXCompressionInfo:
    """Store a node and its accumulated string length without validation.

    Attributes:
        node: Node supplied by the caller; no runtime type check is performed.
        total_string_length: Accumulated length supplied by the caller.

    The generated dataclass constructor requires both arguments. Historical
    field annotations and mutable record behavior are retained for compatibility.
    Instances have no synchronization; callers must coordinate shared mutations.
    """

    node: None
    total_string_length: 0
