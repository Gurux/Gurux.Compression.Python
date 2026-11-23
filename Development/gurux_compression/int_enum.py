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
"""Retain the legacy integer-enum base and its historical import fallback."""

# #pylint: disable=broad-except
try:
    from enum import IntEnum

    class GXIntEnum(IntEnum):
        """Subclass enum.IntEnum to declare legacy integer-valued members.

        Member construction, conversion and validation follow enum.IntEnum.
        The empty base declares no members and retains its original identity.
        """

except Exception:

    class GXIntEnum(int):
        """Use int construction when the standard enum import fails.

        This historical fallback preserves integer behavior but does not
        implement enumeration membership or enum iteration.
        """
