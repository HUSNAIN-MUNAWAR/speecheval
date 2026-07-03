from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class ExecutionProfile:
    id: str
    display_name: str
    capabilities: tuple[str, ...]
    max_concurrency: int
    timeout_seconds: int
    min_ram_gb: int
    gpu_required: bool
    max_audio_duration_seconds: int
    max_upload_size_mb: int


PROFILES = {
    "local-cpu-lightweight": ExecutionProfile(
        id="local-cpu-lightweight",
        display_name="Local CPU — Lightweight",
        capabilities=(
            "audio_validation", "duration", "silence_ratio", "clipping", "loudness",
            "pitch_prosody", "speech_rate", "text_normalization", "wer", "cer", "performance",
        ),
        max_concurrency=1,
        timeout_seconds=1200,
        min_ram_gb=4,
        gpu_required=False,
        max_audio_duration_seconds=300,
        max_upload_size_mb=100,
    ),
    "local-cpu": ExecutionProfile(
        id="local-cpu",
        display_name="Local CPU — Standard",
        capabilities=(
            "audio_validation", "duration", "silence_ratio", "clipping", "loudness",
            "pitch_prosody", "speech_rate", "text_normalization", "wer", "cer", "performance",
        ),
        max_concurrency=1,
        timeout_seconds=3600,
        min_ram_gb=8,
        gpu_required=False,
        max_audio_duration_seconds=900,
        max_upload_size_mb=250,
    ),
    "worker-standard": ExecutionProfile(
        id="worker-standard",
        display_name="Worker — Standard",
        capabilities=("audio_validation", "duration", "silence_ratio", "clipping", "loudness", "pitch_prosody", "speech_rate", "text_normalization", "wer", "cer", "performance"),
        max_concurrency=2,
        timeout_seconds=3600,
        min_ram_gb=8,
        gpu_required=False,
        max_audio_duration_seconds=900,
        max_upload_size_mb=250,
    ),
    "worker-asr": ExecutionProfile(
        id="worker-asr",
        display_name="Worker — ASR capable",
        capabilities=("audio_validation", "duration", "silence_ratio", "clipping", "loudness", "pitch_prosody", "speech_rate", "text_normalization", "wer", "cer", "performance"),
        max_concurrency=1,
        timeout_seconds=7200,
        min_ram_gb=16,
        gpu_required=False,
        max_audio_duration_seconds=1800,
        max_upload_size_mb=500,
    ),
    "gpu-optional": ExecutionProfile(
        id="gpu-optional",
        display_name="GPU — Optional enhancement",
        capabilities=("audio_validation", "duration", "silence_ratio", "clipping", "loudness", "pitch_prosody", "speech_rate", "text_normalization", "wer", "cer", "performance"),
        max_concurrency=1,
        timeout_seconds=7200,
        min_ram_gb=16,
        gpu_required=False,
        max_audio_duration_seconds=1800,
        max_upload_size_mb=500,
    ),
}


def get_profile(profile_id: str) -> ExecutionProfile:
    try:
        return PROFILES[profile_id]
    except KeyError as exc:
        raise ValueError(f"Unknown execution profile '{profile_id}'.") from exc


def serialize_profile(profile: ExecutionProfile) -> dict[str, object]:
    payload = asdict(profile)
    payload["capabilities"] = list(profile.capabilities)
    return payload
