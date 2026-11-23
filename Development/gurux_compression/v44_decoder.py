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
"""Strict V.44 decoding with bounded history and caller-owned binary streams."""

# Protocol state and detached snapshots intentionally span these fields/helpers.
# pylint: disable=protected-access,too-many-instance-attributes,too-many-arguments,too-many-positional-arguments,too-many-branches,too-many-statements

import io
from gettext import gettext as _
from typing import BinaryIO, Callable, Optional, Tuple, Union

from ._bit_array import _BitArray
from ._bit_reader import _BitReader
from ._stream_io import validate_streams, write_all
from .enums import Operation
from .invalid_data_error import InvalidDataError
from .v44_decoder_entry import V44DecoderEntry
from .v44_options import V44Options
from .v44_trace_args import V44TraceArgs


class V44Decoder:
    """Decode complete V.44 streams using an independent validated options copy.

    Instances are synchronous and not thread-safe. Set on_trace to a callable
    accepting a detached V44TraceArgs. Setting event.stop cancels processing
    with InterruptedError. I/O and callback exceptions propagate unchanged.
    """

    def __init__(self, options: Optional[V44Options] = None) -> None:
        """Validate and copy limits, allocating history only as bytes are decoded."""
        self._options = (V44Options() if options is None else options)._snapshot()
        self.on_trace: Optional[Callable[[V44TraceArgs], None]] = None
        self._strings = []
        self._history = bytearray()
        self._previous_type = Operation.NONE
        self._previous_codeword = self._previous_ordinal = 0
        self._last_value_position = 0
        self._ordinal_size = self._options.default_ordinal_size
        self._codeword_size = self._options.default_codeword_size

    @property
    def ordinal_size(self) -> int:
        """Return the current literal bit width, restored on REINIT."""
        return self._ordinal_size

    @property
    def codeword_size(self) -> int:
        """Return the current codeword bit width, restored on REINIT."""
        return self._codeword_size

    @property
    def string_collection(self) -> Tuple[V44DecoderEntry, ...]:
        """Return detached dictionary entries and materialize captured values."""
        return tuple(entry._snapshot() for entry in self._strings)

    def clear_diagnostics(self) -> None:
        """Release diagnostic values while retaining dictionary metadata."""
        for entry in self._strings:
            entry.value = None

    def _reset(self):
        """Clear history, dictionaries and token context; restore initial widths."""
        self._strings.clear()
        self._history.clear()
        self._previous_type = Operation.NONE
        self._previous_codeword = self._previous_ordinal = 0
        self._last_value_position = 0
        self._ordinal_size = self._options.default_ordinal_size
        self._codeword_size = self._options.default_codeword_size

    def _notify(self, operation, value, compressed, index, started=True):
        """Publish detached history and dictionary snapshots when tracing is on."""
        callback = self.on_trace
        if callback is None:
            return
        event = V44TraceArgs(
            operation=operation,
            value=value,
            compressed=compressed,
            index=index,
            uncompressed=bytes(self._history) if started else None,
            string_collection=self.string_collection,
        )
        callback(event)  # pylint: disable=not-callable
        if event.stop:
            raise InterruptedError(_("Decompression stopped by trace callback."))

    def _append_history(self, value):
        """Append a decoded byte while enforcing the negotiated history bound."""
        if len(self._history) >= self._options.history_limit:
            raise InvalidDataError(_("Decoder history overflow before REINIT."))
        self._history.append(value)

    def _add_new_string(self, length, last_position=None):
        """Add a dictionary entry when both string and codeword capacity permit."""
        if (
            length > int(self._options.maximum_string_length)
            or 4 + len(self._strings) >= self._options.max_codewords
        ):
            return
        if last_position is None:
            last_position = len(self._history) - 1
        entry = V44DecoderEntry(4 + len(self._strings), last_position, length)
        count = max(0, len(self._history) - self._last_value_position)
        entry._diagnostic.capture(
            self._history, self._last_value_position, count, self._options.hex
        )
        self._last_value_position = len(self._history)
        self._strings.append(entry)

    def _string_length(self, codeword):
        """Return a stored string length or the next codeword's inferred length."""
        if codeword == 4 + len(self._strings):
            if self._previous_type == Operation.CODEWORD:
                return self._string_length(self._previous_codeword) + 1
            if self._previous_type == Operation.ORDINAL:
                return 2
        if not 4 <= codeword < 4 + len(self._strings):
            raise InvalidDataError(_("Dictionary codeword does not exist."))
        return self._strings[codeword - 4].length

    def _copy_history(self, start, length):
        """Copy a dictionary string, permitting protocol-defined overlap."""
        for index in range(start, start + length):
            if index < 0 or index >= len(self._history):
                raise InvalidDataError(
                    _("Dictionary reference exceeds decoded history.")
                )
            self._append_history(self._history[index])

    def _process_ordinal(self, value):
        """Append a literal and create the previous token's dictionary string."""
        self._append_history(value)
        if self._previous_type == Operation.ORDINAL:
            self._add_new_string(2)
        elif self._previous_type == Operation.CODEWORD:
            self._add_new_string(self._string_length(self._previous_codeword) + 1)
        self._previous_type = Operation.ORDINAL
        self._previous_ordinal = value

    def _process_codeword(self, codeword):
        """Validate and expand a stored or next-to-be-created dictionary code."""
        next_codeword = 4 + len(self._strings)
        if not 4 <= codeword < self._options.max_codewords or codeword > next_codeword:
            raise InvalidDataError(_("Codeword exceeds the negotiated dictionary."))
        if codeword == next_codeword:
            if self._previous_type not in (Operation.ORDINAL, Operation.CODEWORD):
                raise InvalidDataError(
                    _("Uncreated codeword requires a preceding token.")
                )
            if self._previous_type == Operation.CODEWORD and self._string_length(
                self._previous_codeword
            ) >= int(self._options.maximum_string_length):
                raise InvalidDataError(
                    _("Uncreated codeword exceeds maximum string length.")
                )
        output_start = len(self._history)
        if codeword < next_codeword:
            entry = self._strings[codeword - 4]
            self._copy_history(entry.start_position, entry.length)
        elif self._previous_type == Operation.ORDINAL:
            self._append_history(self._previous_ordinal)
            self._append_history(self._previous_ordinal)
        else:
            entry = self._strings[self._previous_codeword - 4]
            self._copy_history(entry.start_position, entry.length)
            self._append_history(self._history[entry.start_position])

        if self._previous_type == Operation.ORDINAL:
            self._add_new_string(2, output_start)
        elif self._previous_type == Operation.CODEWORD:
            self._add_new_string(
                self._string_length(self._previous_codeword) + 1, output_start
            )
        self._previous_type = Operation.CODEWORD
        self._previous_codeword = codeword

    def _process_extension(self, length):
        """Expand bytes after the referenced segment and add its extended string."""
        if self._previous_type != Operation.CODEWORD:
            raise InvalidDataError(_("String extension must follow a codeword."))
        if not 4 <= self._previous_codeword < 4 + len(self._strings):
            raise InvalidDataError(_("Previous codeword was not found."))
        entry = self._strings[self._previous_codeword - 4]
        if entry.length + length > int(self._options.maximum_string_length):
            raise InvalidDataError(_("Extended string exceeds the negotiated maximum."))
        self._copy_history(entry.position + 1, length)
        self._add_new_string(entry.length + length)
        self._previous_type = Operation.STRING_EXTENSION

    def _read_extension(self, reader):
        """Read all extension subfields and reject reserved or excessive lengths."""
        if reader.read(1):
            return 1
        short_length = reader.read(2)
        if short_length:
            return short_length + 1
        if not reader.read(1):
            return reader.read(3) + 5
        width = {46: 5, 78: 6, 142: 7, 255: 8}[int(self._options.maximum_string_length)]
        length = reader.read(width) + 13
        if length > int(self._options.maximum_string_length) - 2:
            raise InvalidDataError(_("Invalid string extension length."))
        return length

    def decompress(self, data: Union[bytes, bytearray, memoryview, str]) -> bytes:
        """Decode a complete byte payload or a formatted LSB-first bit string.

        Bit strings may contain spaces, CR, LF, dashes and braces. Other text
        characters raise ValueError. Malformed, empty or incomplete compressed
        bytes raise InvalidDataError, a ValueError subclass. FLUSH is required.
        """
        if isinstance(data, str):
            digits = []
            for character in data:
                if character in "01":
                    digits.append(character)
                elif character not in " \r\n-{}":
                    raise ValueError(
                        _("Invalid binary character: {character}").format(
                            character=character
                        )
                    )
            bits = _BitArray()
            bits.add("".join(digits))
            data = bits.array()
        elif isinstance(data, (bytes, bytearray, memoryview)):
            data = bytes(data)
        else:
            raise TypeError(_("Expected bytes or binary text."))
        trace_bits = None
        if self.on_trace is not None:
            bits = _BitArray()
            bits.add(data)
            trace_bits = bits.to_bit_string()
        output = io.BytesIO()
        self._decompress_core(io.BytesIO(data), output, trace_bits)
        return output.getvalue()

    def decompress_stream(self, source: BinaryIO, target: BinaryIO) -> None:
        """Synchronously decode binary streams without closing or seeking them.

        Short reads and partial writes are supported. Completed history blocks
        may be written before a malformed later token or I/O failure. A final
        FLUSH is mandatory; FLUSH preserves the dictionary, REINIT clears it.
        InvalidDataError denotes malformed input; stream and callback errors
        propagate unchanged. The streams must be distinct and blocking.
        """
        self._decompress_core(source, target, None)

    def _decompress_core(self, source, target, trace_bits):
        """Decode token boundaries, write completed histories and enforce FLUSH."""
        validate_streams(source, target)
        self._reset()
        reader = _BitReader(source)
        self._notify(Operation.START, None, trace_bits, 0, started=False)
        for operation, value, position in self._decode_events(reader, target):
            self._notify(operation, value, trace_bits, position)

    def _decode_events(self, reader, target):
        """Yield parser events so caller callbacks run outside error handling."""
        after_codeword = ended_with_flush = False
        written = 0
        try:
            while reader.peek() is not None:
                ended_with_flush = False
                prefix = reader.read(1)
                if after_codeword and prefix == 0:
                    if reader.read(1):
                        self._process_extension(self._read_extension(reader))
                        after_codeword = False
                        continue
                after_codeword = False
                if prefix == 0:
                    self._process_ordinal(reader.read(self._ordinal_size))
                    continue
                code = reader.read(self._codeword_size)
                if code == 0:
                    raise InvalidDataError(_("Transparent mode is not supported."))
                if code == 1:
                    reader.align()
                    write_all(target, memoryview(self._history)[written:])
                    written = len(self._history)
                    yield Operation.FLUSH, None, reader.position
                    ended_with_flush = True
                elif code == 2:
                    next_prefix = reader.peek()
                    if next_prefix is None:
                        raise InvalidDataError(_("STEPUP requires a following token."))
                    if next_prefix == 0:
                        if self._ordinal_size == 8:
                            raise InvalidDataError(
                                _("Ordinal width exceeds eight bits.")
                            )
                        self._ordinal_size += 1
                        operation = Operation.STEP_UP_ORDINAL
                    else:
                        maximum = max(
                            self._options.default_codeword_size,
                            (self._options.max_codewords - 1).bit_length(),
                        )
                        if self._codeword_size >= maximum:
                            raise InvalidDataError(
                                _("Codeword width exceeds the dictionary limit.")
                            )
                        self._codeword_size += 1
                        operation = Operation.STEP_UP_CODEWORD
                    yield operation, None, reader.position
                elif code == 3:
                    write_all(target, memoryview(self._history)[written:])
                    written = 0
                    self._reset()
                    yield Operation.REINIT, None, reader.position
                else:
                    self._process_codeword(code)
                    after_codeword = True
            if not ended_with_flush:
                raise InvalidDataError(_("Compressed data must end with FLUSH."))
        except InvalidDataError as error:
            yield Operation.ERROR, str(error), reader.position
            raise
        yield Operation.END, None, reader.position
