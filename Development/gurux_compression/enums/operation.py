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


class Operation(IntEnum):
    """
    Control codes used to indicate specific states or actions during an
    operation such as compression or data processing.
    """

    NONE = -3
    """Indicates that no preceding token has been processed."""
    START = -2
    """Indicates the start of an operation, such as compression or decompression."""
    END = -1
    """Indicates the end of an operation, such as compression or decompression."""
    ORDINAL = 0
    """Represents an ordinal value in the operation."""
    CODEWORD = 1
    """Represents a codeword in the operation."""
    STRING_EXTENSION = 2
    """Indicates a string extension in the operation."""
    STEP_UP_ORDINAL = 3
    """Indicates a step-up ordinal in the operation."""
    STEP_UP_CODEWORD = 4
    """Indicates a step-up codeword in the operation."""
    FLUSH = 5
    """Indicates a flush operation."""
    REINIT = 6
    """Indicates a reinitialization operation."""
    ERROR = 7
    """Indicates an error in the operation."""
    PROCESSING = 8
    """Indicates that the operation is in progress."""
