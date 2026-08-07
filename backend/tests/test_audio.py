import wave
from io import BytesIO

from app.utils.audio import pcm16_to_wav


def test_produces_a_valid_wav_file_wave_module_can_read() -> None:
    pcm = b"\x00\x01" * 100  # 100 fake 16-bit samples

    wav_bytes = pcm16_to_wav(pcm, sample_rate=16_000, channels=1)

    with wave.open(BytesIO(wav_bytes), "rb") as wf:
        assert wf.getframerate() == 16_000
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.readframes(wf.getnframes()) == pcm
