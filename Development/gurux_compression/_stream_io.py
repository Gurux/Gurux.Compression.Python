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
"""Binary stream validation and complete blocking reads/writes."""

from gettext import gettext as _


def validate_streams(source, target) -> None:
    """Require distinct readable/writable binary streams without closing them."""
    if source is target:
        raise ValueError(_("Input and output streams must be different."))
    if not callable(getattr(source, "read", None)) or (
        hasattr(source, "readable") and not source.readable()
    ):
        raise ValueError(_("A readable input stream is required."))
    if not callable(getattr(target, "write", None)) or (
        hasattr(target, "writable") and not target.writable()
    ):
        raise ValueError(_("A writable output stream is required."))


def read_bytes(source, count: int) -> bytes:
    """Read at most count bytes; propagate I/O errors and reject nonbinary data."""
    data = source.read(count)
    if data is None:
        raise BlockingIOError(_("The input stream would block."))
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError(_("The input stream must return bytes."))
    if len(data) > count:
        raise ValueError(_("The input stream returned more bytes than requested."))
    return bytes(data)


def write_all(target, data) -> None:
    """Write all bytes, honoring partial writes and propagating output errors."""
    view = memoryview(data)
    offset = 0
    while offset < len(view):
        written = target.write(view[offset:])
        if written is None or written == 0:
            raise BlockingIOError(_("The output stream made no progress."))
        if not isinstance(written, int) or written < 0 or written > len(view) - offset:
            raise OSError(_("The output stream returned an invalid byte count."))
        offset += written
