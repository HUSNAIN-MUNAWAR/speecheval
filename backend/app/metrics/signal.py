from __future__ import annotations

import math
import struct
import wave
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AudioSignal:
    samples: list[float]
    sample_rate: int
    channels: int
    sample_width: int
    duration_seconds: float


def read_pcm_wav(path: Path) -> AudioSignal:
    with wave.open(str(path), "rb") as source:
        channels = source.getnchannels()
        sample_width = source.getsampwidth()
        sample_rate = source.getframerate()
        frames = source.getnframes()
        compression = source.getcomptype()
        if compression != "NONE":
            raise ValueError(f"Unsupported WAV compression '{compression}'.")
        if channels not in {1, 2}:
            raise ValueError(f"Unsupported channel count {channels}.")
        if sample_width not in {1, 2, 3, 4}:
            raise ValueError(f"Unsupported PCM sample width {sample_width}.")
        raw = source.readframes(frames)
    if not raw:
        raise ValueError("Audio file has no PCM frames.")
    values: list[float]
    if sample_width == 1:
        values = [(value - 128) / 128.0 for value in raw]
    elif sample_width == 2:
        count = len(raw) // 2
        values = [value / 32768.0 for value in struct.unpack(f"<{count}h", raw)]
    elif sample_width == 4:
        count = len(raw) // 4
        values = [value / 2147483648.0 for value in struct.unpack(f"<{count}i", raw)]
    else:
        values = []
        for index in range(0, len(raw), 3):
            value = int.from_bytes(raw[index:index + 3], byteorder="little", signed=True)
            values.append(value / 8388608.0)
    if channels == 2:
        values = [(values[index] + values[index + 1]) / 2 for index in range(0, len(values) - 1, 2)]
    duration = len(values) / sample_rate
    return AudioSignal(values, sample_rate, channels, sample_width, duration)


def rms(values: list[float]) -> float:
    return math.sqrt(sum(value * value for value in values) / max(1, len(values)))


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    position = (len(sorted_values) - 1) * q
    lower = int(position)
    upper = min(len(sorted_values) - 1, lower + 1)
    fraction = position - lower
    return sorted_values[lower] * (1 - fraction) + sorted_values[upper] * fraction


def estimate_pitch_hz(signal: AudioSignal, min_hz: float = 70, max_hz: float = 350) -> tuple[float | None, float]:
    # Lightweight normalized autocorrelation. It is a prosody proxy, not an emotion classifier.
    if len(signal.samples) < signal.sample_rate // 4:
        return None, 0.0
    frame_size = min(len(signal.samples), int(signal.sample_rate * 0.08))
    frame = signal.samples[:frame_size]
    energy = rms(frame)
    if energy < 0.005:
        return None, 0.0
    min_lag = max(1, int(signal.sample_rate / max_hz))
    max_lag = min(frame_size // 2, int(signal.sample_rate / min_hz))
    best_lag, best_score = 0, -1.0
    for lag in range(min_lag, max_lag + 1):
        a, b = frame[:-lag], frame[lag:]
        denominator = math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))
        score = sum(x * y for x, y in zip(a, b, strict=True)) / denominator if denominator else 0.0
        if score > best_score:
            best_lag, best_score = lag, score
    return (signal.sample_rate / best_lag if best_lag else None), max(0.0, best_score)
