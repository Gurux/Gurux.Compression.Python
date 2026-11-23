# Gurux Compression for Python

V.44 compression and decompression matching Gurux.Compression.Net, implemented
with Python's standard library. Requires Python 3.7 or newer, consistent with the
existing implementation's dataclass requirement. Runtime dependencies: none.

## Installation

Install `gurux_compression` from PyPI:

```shell
python -m pip install gurux_compression
```

## Byte and text API

```python
from gurux_compression import V44Decoder, V44Encoder, V44Options

options = V44Options(history_limit=4096, max_codewords=4096)
encoder = V44Encoder(options)
decoder = V44Decoder(options)
original = b"ABCDEXABCDEYABCDE"
wire = encoder.compress(original)
assert decoder.decompress(wire) == original
assert decoder.decompress(encoder.compress(b"")) == b""
```

`compress()` accepts bytes, bytearray, memoryview, or ASCII text. Non-ASCII text
raises UnicodeEncodeError; encode other text explicitly before compression.
`decompress()` accepts bytes-like input or an LSB-first binary string, allowing
spaces, CR, LF, dashes and braces as formatting. Both methods return bytes.
Malformed or incomplete input raises `InvalidDataError`, a `ValueError` subclass.
A complete message must end in FLUSH with zero alignment padding. FLUSH preserves
the dictionary across aligned packets; REINIT clears history and restores widths.
Empty source data produces a valid FLUSH-only message.

## Binary streams

```python
from gurux_compression import V44Decoder, V44Encoder

with open("input.bin", "rb") as source, open("compressed.v44", "wb") as target:
    V44Encoder().compress_stream(source, target)
with open("compressed.v44", "rb") as source, open("restored.bin", "wb") as target:
    V44Decoder().decompress_stream(source, target)
```

The synchronous stream methods support nonseekable streams, short reads and
partial writes. They leave both handles open and do not flush or seek them.
Source and target must be different blocking binary streams. Compression uses
blocks of at most `min(history_limit, 65536)` bytes. Decoding retains at most one
negotiated history plus a small input buffer. Completed blocks may already be
written when later input is malformed or an I/O error occurs. Stream and callback
exceptions propagate to the caller.

Array and stream compression produce identical bytes within one stream block.
For larger messages their REINIT placement may differ; both formats interoperate
with both APIs in Python and .NET.

## Options and diagnostics

`V44Options` provides these fields:

| Field | Default | Accepted values |
| --- | --- | --- |
| `default_codeword_size` | 6 | 6â€“16 bits |
| `default_ordinal_size` | 7 | 7 or 8 bits |
| `max_codewords` | 1024 | 256â€“65535, including four control codes |
| `maximum_string_length` | `MaximumStringLength.VALUE_255` | VALUE_46, VALUE_78, VALUE_142, VALUE_255 |
| `history_limit` | 3072 | 512â€“2147483647 bytes |
| `hex` | False | Boolean diagnostic formatting switch |

Call `options.validate()` to check values explicitly. Each codec validates and
copies options at construction; later changes affect only subsequently created
codecs. Required REINIT controls are always emitted. Unused legacy options are
removed. Codec instances are reusable but are not thread-safe.

`encoder.node_tree` and `decoder.string_collection` return tuples of detached
`V44Node` and `V44DecoderEntry` snapshots. `encoder.get_root_array()` returns
populated `(root_byte, codeword)` pairs. `ordinal_size` and `codeword_size` are
read-only current widths. `encoder.reset()` clears its dictionary and restores
initial widths. `clear_diagnostics()` on either codec releases retained diagnostic
bytes/text while preserving dictionary metadata; previously captured snapshots
remain valid. Diagnostic text is formatted only when inspected.

```python
from gurux_compression import Operation, V44Encoder


def trace(event):
    print(event.operation, event.index)
    # Set event.stop = True to cancel with InterruptedError.


encoder = V44Encoder()
encoder.on_trace = trace
encoder.compress(b"ABABX")
```

Each `V44TraceArgs` is detached from codec state. Byte payloads and compressed bit
strings are immutable; exported dictionary objects can be edited without changing
the codec. Stream decoder events have `compressed=None`; byte decoder events
include the full padded input bits. Encoder events contain exactly the emitted
bits without padding. Callbacks may raise exceptions directly to abort processing.
Set `on_trace=None` to disable snapshot construction.

## Naming migration

This update deliberately removes the old API without aliases or deprecated
wrappers. Methods, fields and module names use snake_case; classes use PascalCase.

| Previous API | Current API |
| --- | --- |
| `GXV44Encoder` | `V44Encoder` |
| `GXV44Decoder` | `V44Decoder` |
| `GXv44Options` | `V44Options` |
| `GXv44Node` | `V44Node` |
| `GXv44DecoderEntry` | `V44DecoderEntry` |
| `GXV44TraceArgs` | `V44TraceArgs` |
| `GXBitArray`, `BitArray` | Internal; use `str` for bit strings and `bytes` for packed data |
| `GXByteBuffer`, `ByteBuffer` | Removed; use `bytes`, `bytearray`, `struct` and `bytes.fromhex()` |
| `add_listener()` / `remove_listener()` / `IGXCompressionListener` | Assign `on_trace` to a callable accepting one event, or None |
| `node.type` | `node.operation` |
| `entry.start_pos` | `entry.start_position` |
| Diagnostic `to_string()` | Python `str(object)` |
| `max_dictionary_size`, `emit_reinit_control` | Removed; use `max_codewords`; required REINIT is unconditional |
| `GXCompressionInfo`, `GXIntEnum` | Removed implementation helpers; enums use `enum.IntEnum` |

`BitArray` is now an internal codec implementation detail and is no longer
exported. The old `gurux_compression.bit_array` module is removed. Represent
bit sequences as strings such as `"101"`. Trace events already expose
`compressed` as a bit string (or `None` for streamed decoding), and
`decompress()` accepts LSB-first bit strings. A bit string must contain a
complete valid V.44 packet to be decoded; `"101"` only illustrates the text
format. `compress()` continues to return packed `bytes`.
`ByteBuffer` and the `gurux_compression.byte_buffer` module have been removed
from the library. Use `bytes`/`bytearray`, `struct` for numeric fields,
`bytes.fromhex()` for hexadecimal input, and Python binary streams. The private
fixture buffer in the test suite is not part of the library API.

## License

GPL-2.0-only OR LicenseRef-Gurux-Commercial. See `LICENSE` for GPL version 2 and
`LICENSES/LicenseRef-Gurux-Commercial` for commercial licensing contact information.
Gurux: <https://www.gurux.fi/>.
