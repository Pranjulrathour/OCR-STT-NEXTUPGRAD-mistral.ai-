"""Minimal PCM16 -> WAV header wrapping.

Mistral's batch transcription endpoint wants a real audio file (it sniffs
the container), not headerless raw PCM — this bolts on the 44-byte WAV
header needed to make the buffered realtime audio replayable through that
endpoint for the post-stop accuracy refinement pass.
"""

from __future__ import annotations

import struct


def pcm16_to_wav(pcm_bytes: bytes, *, sample_rate: int, channels: int = 1) -> bytes:
    bits_per_sample = 16
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    data_size = len(pcm_bytes)

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,  # PCM
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size,
    )
    return header + pcm_bytes
