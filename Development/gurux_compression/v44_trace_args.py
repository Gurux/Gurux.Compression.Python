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
"""Detached events passed to optional V.44 trace callbacks."""

# Protocol state and detached snapshots intentionally span these fields/helpers.
# pylint: disable=too-many-instance-attributes

from dataclasses import dataclass
from typing import Any, Optional, Tuple
from gettext import gettext as _

from .enums import Operation
from .v44_node import V44Node
from .v44_decoder_entry import V44DecoderEntry


@dataclass
class V44TraceArgs:
    """Describe one trace operation independently of mutable codec state.

    Attributes:
        compress: True for encoding and False for decoding.
        operation: Event kind from Operation.
        value: Token metadata or an error description.
        uncompressed: Current block/history bytes, or None at decoder start.
        compressed: Exact transmitted bits, or None for streamed decoding.
        index: Input byte offset or decoder bit offset.
        node_tree: Detached encoder dictionary, when encoding.
        string_collection: Detached decoder dictionary, when decoding.
        stop: Set True in the callback to cancel with InterruptedError.
    """

    compress: bool = False
    operation: Operation = Operation.NONE
    value: Any = None
    uncompressed: Optional[bytes] = None
    compressed: Optional[str] = None
    index: int = 0
    node_tree: Optional[Tuple[V44Node, ...]] = None
    string_collection: Optional[Tuple[V44DecoderEntry, ...]] = None
    stop: bool = False

    def __str__(self) -> str:
        """Return a readable description of the captured operation."""
        if self.operation == Operation.START:
            return _("Compress Start") if self.compress else _("Decompress Start")
        if self.operation == Operation.END:
            return _("Compress End") if self.compress else _("Decompress End")
        if self.operation in (
            Operation.ORDINAL,
            Operation.CODEWORD,
            Operation.STRING_EXTENSION,
        ):
            return str(self.value)
        if self.operation == Operation.PROCESSING:
            return f"CW({self.value})"
        descriptions = {
            Operation.STEP_UP_ORDINAL: _("StepUp Ordinal"),
            Operation.STEP_UP_CODEWORD: _("StepUp Codeword"),
            Operation.FLUSH: _("Flush"),
            Operation.REINIT: _("ReInit"),
            Operation.ERROR: _("Error"),
        }
        return descriptions.get(self.operation, self.operation.name)
