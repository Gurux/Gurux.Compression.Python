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
"""V.44 compression with bounded history and optional detached diagnostics."""

# Protocol state and detached snapshots intentionally span these fields/helpers.
# pylint: disable=duplicate-code,protected-access,too-many-instance-attributes,too-many-arguments,too-many-positional-arguments,too-many-branches,too-many-statements

from typing import BinaryIO, Callable, Optional, Tuple, Union
from gettext import gettext as _

from ._bit_array import _BitArray
from ._bit_writer import _BitWriter
from ._stream_io import read_bytes, validate_streams
from .enums import Operation
from .v44_node import V44Node
from .v44_options import V44Options
from .v44_trace_args import V44TraceArgs


class V44Encoder:
    """Compress independent V.44 messages using a validated options snapshot.

    Instances are synchronous and not thread-safe. Set on_trace to a callable
    receiving a detached V44TraceArgs; setting event.stop cancels processing
    with InterruptedError. Exceptions from callbacks and streams propagate.
    """

    def __init__(self, options: Optional[V44Options] = None) -> None:
        """Validate and copy options; use default limits when options is None."""
        self._options = (V44Options() if options is None else options)._snapshot()
        self.hex = self._options.hex
        self.on_trace: Optional[Callable[[V44TraceArgs], None]] = None
        self._compressed = _BitArray()
        self._nodes = []
        self._roots = [0] * 256
        self._ordinal_size = self._options.default_ordinal_size
        self._codeword_size = self._options.default_codeword_size

    @property
    def ordinal_size(self) -> int:
        """Return the current literal width, restored on REINIT or reset."""
        return self._ordinal_size

    @property
    def codeword_size(self) -> int:
        """Return the current dictionary-code width, restored on reset."""
        return self._codeword_size

    @property
    def node_tree(self) -> Tuple[V44Node, ...]:
        """Return detached diagnostic nodes, materializing their formatted values."""
        return tuple(node._snapshot() for node in self._nodes)

    def get_root_array(self) -> Tuple[Tuple[int, int], ...]:
        """Return detached root-byte/codeword pairs for populated roots."""
        return tuple((index, code) for index, code in enumerate(self._roots) if code)

    def clear_diagnostics(self) -> None:
        """Release captured data and values while preserving dictionary metadata."""
        for node in self._nodes:
            node.value = ""

    def reset(self) -> None:
        """Clear dictionaries and restore the configured initial bit widths."""
        self._roots = [0] * 256
        self._nodes.clear()
        self._ordinal_size = self._options.default_ordinal_size
        self._codeword_size = self._options.default_codeword_size

    def _notify(self, operation, data, block, index):
        """Publish an independent event only when a callback is configured."""
        callback = self.on_trace
        if callback is None:
            return
        event = V44TraceArgs(
            compress=True,
            operation=operation,
            value=data._snapshot() if isinstance(data, V44Node) else data,
            uncompressed=bytes(block),
            compressed=self._compressed.to_bit_string(),
            index=index,
            node_tree=self.node_tree,
        )
        callback(event)  # pylint: disable=not-callable
        if event.stop:
            raise InterruptedError(_("Compression stopped by trace callback."))

    def _add_string_extension_length(self, bits, length):
        """Encode a valid extension length using the negotiated V.44 subfields."""
        if not 1 <= length <= int(self._options.maximum_string_length) - 2:
            raise ValueError(_("Invalid string extension length."))
        if length == 1:
            bits.add(1, 1)
        elif length <= 4:
            bits.add(0, 1)
            bits.add(length - 1, 2)
        elif length <= 12:
            bits.add((length - 5) << 4, 7)
        else:
            width = {46: 5, 78: 6, 142: 7, 255: 8}[
                int(self._options.maximum_string_length)
            ]
            bits.add(8, 4)
            bits.add(length - 13, width)

    def _write_ordinal(self, value, previous):
        """Emit a literal with STEPUP or post-codeword prefix when required."""
        if value.bit_length() > self._ordinal_size:
            self._compressed.add(1, 1)
            self._compressed.add(2, self._codeword_size)
            self._ordinal_size += 1
        elif previous == Operation.CODEWORD:
            self._compressed.add(0, 1)
        self._compressed.add(0, 1)
        self._compressed.add(value, self._ordinal_size)

    def _write_string(self, codeword, extension):
        """Emit all required width increases, a codeword and optional extension."""
        self._compressed.add(1, 1)
        while codeword.bit_length() > self._codeword_size:
            self._compressed.add(2, self._codeword_size)
            self._codeword_size += 1
            self._compressed.add(1, 1)
        self._compressed.add(codeword, self._codeword_size)
        if extension:
            self._compressed.add(2, 2)
            self._add_string_extension_length(self._compressed, extension)

    def _find_match(self, codeword, data, cursor, history_end, input_end):
        """Traverse child/sibling segments, respecting input and string bounds."""
        best, matched = None, 0
        level = self._nodes[codeword - 4]
        maximum = int(self._options.maximum_string_length)
        while level is not None:
            while True:
                length = level.length
                if (
                    1 + matched + length <= maximum
                    and cursor + length <= input_end
                    and level.position + length <= history_end
                    and data[cursor : cursor + length]
                    == data[level.position : level.position + length]
                ):
                    break
                if not level.side_index:
                    return best, 1 + matched if best is not None else 0
                level = self._nodes[level.side_index - 4]
            best = level
            matched += level.length
            cursor += level.length
            level = self._nodes[level.down_index - 4] if level.down_index else None
        return best, 1 + matched

    def _link_sibling(self, first, node):
        """Append a dictionary segment to an existing sibling chain."""
        current = self._nodes[first - 4]
        while current.side_index:
            current = self._nodes[current.side_index - 4]
        current.side_index = node.codeword

    def _link_child(self, parent, node):
        """Attach a new child segment, retaining previous child siblings."""
        if parent.down_index:
            self._link_sibling(parent.down_index, node)
        else:
            parent.down_index = node.codeword

    def _new_node(self, position, length, data, start, count, operation):
        """Construct metadata retaining diagnostic bytes only until inspected."""
        node = V44Node(4 + len(self._nodes), position, length)
        node.operation = operation
        node._diagnostic.capture(data, start, count, self.hex)
        return node

    def _compress_block(self, data, flush):
        """Encode a block without copying history; optionally append final FLUSH."""
        self._compressed.size = 0
        self.reset()
        history_end = index = 0
        input_end = min(len(data), self._options.history_limit)
        previous = Operation.ORDINAL
        self._notify(Operation.START, None, data, 0)
        while index < len(data):
            if (
                index == input_end
                or 4 + len(self._nodes) >= self._options.max_codewords
            ):
                self._compressed.add(1, 1)
                self._compressed.add(3, self._codeword_size)
                self.reset()
                history_end = index
                input_end = min(len(data), index + self._options.history_limit)
                previous = Operation.NONE
                self._notify(Operation.REINIT, None, data, index)

            value = data[index]
            history_end += 1
            root = self._roots[value]
            matched, consumed = (
                self._find_match(root, data, index + 1, history_end, input_end)
                if root
                else (None, 0)
            )
            if matched is None:
                self._write_ordinal(value, previous)
                previous = Operation.ORDINAL
                node = self._new_node(index + 1, 1, data, index, 1, previous)
                self._nodes.append(node)
                if root:
                    self._notify(Operation.ORDINAL, node, data, index)
                if index + 1 < len(data):
                    if root:
                        self._link_sibling(root, node)
                    else:
                        self._roots[value] = node.codeword
                index += 1
                if not root:
                    self._notify(Operation.ORDINAL, node, data, index)
                continue

            history_end += consumed - 1
            extension = 0
            source = matched.position + matched.length
            maximum = int(self._options.maximum_string_length) - consumed
            while (
                extension < maximum
                and index + consumed + extension < input_end
                and source + extension < history_end
                and data[index + consumed + extension] == data[source + extension]
            ):
                history_end += 1
                extension += 1

            if extension:
                node = self._new_node(
                    index + consumed,
                    extension,
                    data,
                    index,
                    consumed + extension,
                    Operation.STRING_EXTENSION,
                )
                self._link_child(matched, node)
                self._nodes.append(node)
                self._write_string(matched.codeword, extension)
                self._notify(Operation.PROCESSING, matched.codeword, data, 0)
                previous = Operation.STRING_EXTENSION
                consumed += extension
            else:
                self._write_string(matched.codeword, 0)
                node = self._new_node(
                    index + consumed, 1, data, index, consumed, Operation.CODEWORD
                )
                if consumed < int(self._options.maximum_string_length):
                    self._link_child(matched, node)
                    self._nodes.append(node)
                self._notify(Operation.CODEWORD, node, data, 0)
                self._notify(Operation.PROCESSING, matched.codeword, data, 0)
                previous = Operation.CODEWORD
            index += consumed

        if flush:
            self._compressed.add(1, 1)
            self._compressed.add(1, self._codeword_size)
        self._notify(Operation.END, None, data, 0)

    def compress(self, data: Union[bytes, bytearray, memoryview, str]) -> bytes:
        """Compress bytes or ASCII text into one zero-padded V.44 message.

        Empty input produces FLUSH-only bytes. Unsupported data raises TypeError;
        non-ASCII text raises UnicodeEncodeError. The codec can be reused after
        success, callback cancellation or callback failure.
        """
        if isinstance(data, str):
            data = data.encode("ascii")
        elif isinstance(data, (bytes, bytearray, memoryview)):
            data = bytes(data)
        else:
            raise TypeError(_("Expected bytes or ASCII text."))
        self._compress_block(data, True)
        return self._compressed.array()

    def compress_stream(self, source: BinaryIO, target: BinaryIO) -> None:
        """Synchronously compress binary streams in bounded input blocks.

        Neither stream is closed, flushed or sought. Short reads and partial
        writes are supported. Streams must be distinct and blocking. Completed
        blocks may be written before an I/O error or callback cancellation.
        I/O and callback exceptions propagate unchanged.
        """
        validate_streams(source, target)
        capacity = min(self._options.history_limit, 65536)
        writer = _BitWriter(target)
        pending = b""
        while True:
            block = bytearray(pending)
            while len(block) < capacity:
                chunk = read_bytes(source, capacity - len(block))
                if not chunk:
                    break
                block.extend(chunk)
            pending = read_bytes(source, 1)
            self._compress_block(bytes(block), not pending)
            if pending:
                self._compressed.add(1, 1)
                self._compressed.add(3, self._codeword_size)
            writer.write(self._compressed)
            if not pending:
                break
        writer.align()
