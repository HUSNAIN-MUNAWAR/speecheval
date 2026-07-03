from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psutil

from app.metrics.base import (
    EvaluationContext,
    EvaluationItem,
    MetricDirection,
    MetricResult,
    MetricStatus,
)
from app.metrics.signal import AudioSignal, estimate_pitch_hz, percentile, read_pcm_wav, rms
from app.metrics.text import levenshtein_alignment, normalize_text


@dataclass(slots=True)
class CpuMetricPlugin:
    id: str
    display_name: str
    description: str
    category: str
    direction: MetricDirection
    required_inputs: tuple[str, ...] = ("generated_audio",)
    optional_inputs: tuple[str, ...] = ()
    hardware_requirements: str = "CPU"
    dependency_requirements: tuple[str, ...] = ()
    configuration_schema: dict[str, Any] | None = None
    result_schema: dict[str, Any] | None = None
    aggregation_strategy: str = "mean_median_p95"
    limitations: str = "CPU-first implementation; inspect metric metadata before making a release decision."
    citation: str | None = None
    version: str = "1.0.0"

    def is_available(self, context: EvaluationContext) -> tuple[bool, str | None]:
        return True, None

    def evaluate(self, item: EvaluationItem, context: EvaluationContext) -> list[MetricResult]:
        raise NotImplementedError


def _audio(item: EvaluationItem, context: EvaluationContext) -> AudioSignal:
    if not item.audio_ref:
        raise ValueError("Generated audio artifact is required.")
    return read_pcm_wav(Path(context.storage_root) / item.audio_ref)


def _result(plugin: CpuMetricPlugin, value: float | None, unit: str | None, *, status: MetricStatus = MetricStatus.SUCCESS, metadata: dict[str, Any] | None = None, warnings: list[str] | None = None, confidence: float | None = None, error: str | None = None) -> MetricResult:
    return MetricResult(plugin.id, plugin.version, status, value, unit, metadata or {}, warnings or [], confidence, error)


class AudioValidationPlugin(CpuMetricPlugin):
    def __init__(self):
        super().__init__("audio_validation", "Audio validation", "Verifies decodable PCM WAV artifacts, basic signal properties, and SHA-256.", "audio", MetricDirection.INFORMATIONAL)

    def evaluate(self, item: EvaluationItem, context: EvaluationContext) -> list[MetricResult]:
        start = time.perf_counter()
        if not item.audio_ref:
            return [_result(self, None, None, status=MetricStatus.SKIPPED, warnings=["No generated audio reference provided."])]
        path = Path(context.storage_root) / item.audio_ref
        try:
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError("Audio artifact is missing or zero-byte.")
            signal = read_pcm_wav(path)
            checksum = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
            silent = rms(signal.samples) < 0.001
            return [_result(self, 1.0, "boolean", metadata={
                "valid": True, "format": "wav", "sample_rate": signal.sample_rate,
                "channels": signal.channels, "bit_depth": signal.sample_width * 8,
                "duration_seconds": signal.duration_seconds, "checksum": checksum,
                "waveform_downsample": signal.samples[::max(1, len(signal.samples)//512)][:512],
                "silent": silent, "execution_duration_ms": int((time.perf_counter()-start)*1000),
            }, warnings=["Audio is effectively silent."] if silent else [])]
        except Exception as exc:
            return [_result(self, 0.0, "boolean", status=MetricStatus.FAILED, error=str(exc), metadata={"valid": False})]


class DurationPlugin(CpuMetricPlugin):
    def __init__(self): super().__init__("duration", "Audio duration", "Measures decoded audio duration and text-normalized duration rate.", "audio", MetricDirection.INFORMATIONAL)
    def evaluate(self, item: EvaluationItem, context: EvaluationContext) -> list[MetricResult]:
        signal = _audio(item, context)
        words = len(normalize_text(item.expected_text, item.language).tokens)
        return [_result(self, signal.duration_seconds, "seconds", metadata={"duration_per_word": signal.duration_seconds/max(1, words), "sample_rate":signal.sample_rate})]


class SilenceRatioPlugin(CpuMetricPlugin):
    def __init__(self): super().__init__("silence_ratio", "Silence / voiced ratio", "Frame-based energy threshold silence analysis.", "audio", MetricDirection.LOWER_IS_BETTER)
    def evaluate(self, item: EvaluationItem, context: EvaluationContext) -> list[MetricResult]:
        signal = _audio(item, context)
        frame = max(1, int(signal.sample_rate * 0.02)); threshold = float(context.parameters.get("silence_threshold", 0.012))
        frames = [signal.samples[index:index+frame] for index in range(0, len(signal.samples), frame)]
        silent = [rms(chunk) < threshold for chunk in frames]
        ratio = sum(silent)/max(1,len(silent)); leading = 0; trailing = 0
        for value in silent:
            if not value: break
            leading += 1
        for value in reversed(silent):
            if not value: break
            trailing += 1
        longest = current = 0
        segments: list[dict[str,float]]=[]; begin: int|None=None
        for idx, value in enumerate(silent + [False]):
            if value:
                if begin is None: begin=idx
                current+=1; longest=max(longest,current)
            elif begin is not None:
                segments.append({"start_seconds":begin*frame/signal.sample_rate,"end_seconds":idx*frame/signal.sample_rate})
                begin=None;current=0
        return [_result(self, ratio, "ratio", metadata={"leading_silence_seconds":leading*frame/signal.sample_rate,"trailing_silence_seconds":trailing*frame/signal.sample_rate,"longest_silence_seconds":longest*frame/signal.sample_rate,"voiced_frame_ratio":1-ratio,"silence_segments":segments,"threshold":threshold})]


class ClippingPlugin(CpuMetricPlugin):
    def __init__(self): super().__init__("clipping", "Clipping and peak analysis", "Detects saturated and near-saturated PCM samples.", "audio", MetricDirection.LOWER_IS_BETTER)
    def evaluate(self, item: EvaluationItem, context: EvaluationContext) -> list[MetricResult]:
        signal=_audio(item, context); absolute=[abs(value) for value in signal.samples]
        clipped=sum(value>=0.999 for value in absolute); near=sum(value>=0.98 for value in absolute)
        peak=max(absolute, default=0.0); dynamic=20*math.log10(max(1e-8, percentile(absolute,.95))/max(1e-8, percentile(absolute,.05)))
        return [_result(self, clipped/max(1,len(absolute)), "ratio", metadata={"peak_amplitude":peak,"clipping_sample_count":clipped,"near_clipping_ratio":near/max(1,len(absolute)),"dynamic_range_estimate_db":dynamic,"warning":clipped>0})]


class LoudnessPlugin(CpuMetricPlugin):
    def __init__(self):
        super().__init__(
            "loudness",
            "Integrated loudness",
            "Measures integrated loudness with pyloudnorm when installed; otherwise records an explicit RMS estimate.",
            "audio",
            MetricDirection.TARGET_RANGE,
            dependency_requirements=("pyloudnorm", "numpy"),
            limitations="Short clips or unavailable dependencies use a clearly labeled RMS estimate. Use a calibrated broadcast workflow for certification.",
        )

    def evaluate(self, item: EvaluationItem, context: EvaluationContext) -> list[MetricResult]:
        signal = _audio(item, context)
        target = float(context.parameters.get("target_lufs", -23.0))
        peak = max((abs(value) for value in signal.samples), default=0.0)
        try:
            import numpy as np
            import pyloudnorm as pyln  # type: ignore[import-untyped]

            values = np.asarray(signal.samples, dtype=float)
            # pyloudnorm requires enough audio for the configured gating block.
            measured = float(pyln.Meter(signal.sample_rate).integrated_loudness(values))
            return [
                _result(
                    self,
                    measured,
                    "LUFS",
                    metadata={
                        "integrated_loudness_lufs": measured,
                        "sample_peak": peak,
                        "normalized_loudness_delta": measured - target,
                        "target_lufs": target,
                        "method": "pyloudnorm",
                    },
                )
            ]
        except Exception as exc:
            estimated = 20 * math.log10(max(rms(signal.samples), 1e-9))
            return [
                _result(
                    self,
                    estimated,
                    "LUFS_estimated",
                    status=MetricStatus.ESTIMATED,
                    metadata={
                        "integrated_loudness_estimated_lufs": estimated,
                        "sample_peak": peak,
                        "normalized_loudness_delta": estimated - target,
                        "target_lufs": target,
                        "method": "rms_fallback",
                        "fallback_reason": str(exc),
                    },
                    warnings=["Estimated from PCM RMS; not EBU R128 compliance."],
                )
            ]


class PitchProsodyPlugin(CpuMetricPlugin):
    def __init__(self): super().__init__("pitch_prosody", "Pitch variation proxy", "CPU autocorrelation F0 estimate and voiced-frame stability proxy.", "prosody", MetricDirection.INFORMATIONAL, limitations="F0 is estimated and does not measure emotion, naturalness, or speaker identity.")
    def evaluate(self,item:EvaluationItem,context:EvaluationContext)->list[MetricResult]:
        signal=_audio(item,context); frame=max(1,int(signal.sample_rate*.08)); pitches=[]; confidences=[]
        for start in range(0,len(signal.samples)-frame,frame):
            f0, confidence=estimate_pitch_hz(AudioSignal(signal.samples[start:start+frame],signal.sample_rate,signal.channels,signal.sample_width,frame/signal.sample_rate))
            if f0 is not None: pitches.append(f0);confidences.append(confidence)
        mean=sum(pitches)/len(pitches) if pitches else None
        return [_result(self,mean,"Hz_estimated",status=MetricStatus.ESTIMATED if mean is not None else MetricStatus.SKIPPED,metadata={"mean_f0_hz":mean,"median_f0_hz":percentile(pitches,.5) if pitches else None,"pitch_range_hz":(max(pitches)-min(pitches)) if pitches else None,"pitch_std_hz":math.sqrt(sum((value-mean)**2 for value in pitches)/len(pitches)) if pitches and mean else None,"voiced_ratio":len(pitches)/max(1,len(signal.samples)//frame),"confidence":sum(confidences)/len(confidences) if confidences else 0.0,"series_hz":pitches[:300]},warnings=["Pitch is an estimated prosody proxy."])]


class SpeechRatePlugin(CpuMetricPlugin):
    def __init__(self): super().__init__("speech_rate", "Speech rate", "Computes text-per-duration rates from expected text.", "text", MetricDirection.INFORMATIONAL)
    def evaluate(self,item:EvaluationItem,context:EvaluationContext)->list[MetricResult]:
        signal=_audio(item,context); normalized=normalize_text(item.expected_text,item.language); duration=max(signal.duration_seconds,1e-6); words=len(normalized.tokens)
        return [_result(self,words/duration,"words_per_second",metadata={"words_per_minute":words/duration*60,"characters_per_second":len(normalized.normalized.replace(" ",""))/duration,"duration_per_word":duration/max(1,words),"token_count":words})]


class TextNormalizationPlugin(CpuMetricPlugin):
    def __init__(self): super().__init__("text_normalization", "Text normalization", "Records multilingual baseline normalization trace.", "text", MetricDirection.INFORMATIONAL, required_inputs=("expected_text",))
    def evaluate(self,item:EvaluationItem,context:EvaluationContext)->list[MetricResult]:
        normalized=normalize_text(item.expected_text,item.language)
        return [_result(self,float(len(normalized.tokens)),"tokens",metadata={"raw":normalized.raw,"normalized":normalized.normalized,"tokens":normalized.tokens,"trace":normalized.trace,"language":item.language})]


class WerCerPlugin(CpuMetricPlugin):
    def __init__(self, metric_id: str):
        super().__init__(metric_id,"Word error rate" if metric_id=="wer" else "Character error rate","Scores expected text against a deterministic mock/manual transcript adapter.","transcription",MetricDirection.LOWER_IS_BETTER,required_inputs=("expected_text",),limitations="The default transcript adapter is deterministic mock/manual data, not live ASR. It is explicitly marked MOCK.")
    def evaluate(self,item:EvaluationItem,context:EvaluationContext)->list[MetricResult]:
        transcript=str(item.metadata.get("manual_transcript") or item.metadata.get("mock_transcript") or item.expected_text)
        ref=normalize_text(item.expected_text,item.language); hyp=normalize_text(transcript,item.language)
        reference=list(ref.normalized.replace(" ","")) if self.id=="cer" else ref.tokens
        hypothesis=list(hyp.normalized.replace(" ","")) if self.id=="cer" else hyp.tokens
        insertions,deletions,substitutions,distance,alignment=levenshtein_alignment(reference,hypothesis)
        return [_result(self,distance/max(1,len(reference)),"ratio",status=MetricStatus.MOCK,metadata={"adapter":"MockASRAdapter" if "mock_transcript" in item.metadata else "ManualTranscriptAdapter","raw_reference":item.expected_text,"raw_hypothesis":transcript,"normalized_reference":ref.normalized,"normalized_hypothesis":hyp.normalized,"insertions":insertions,"deletions":deletions,"substitutions":substitutions,"reference_length":len(reference),"hypothesis_length":len(hypothesis),"alignment":alignment},warnings=["Recognition score uses a mock/manual transcript adapter."])]


class PerformancePlugin(CpuMetricPlugin):
    def __init__(self):
        super().__init__(
            "performance",
            "Performance telemetry",
            "Captures worker timing, process RAM, CPU time, and audio real-time factor.",
            "performance",
            MetricDirection.LOWER_IS_BETTER,
        )

    def evaluate(self, item: EvaluationItem, context: EvaluationContext) -> list[MetricResult]:
        signal = _audio(item, context)
        worker_ms = float(item.metadata.get("worker_metric_elapsed_ms", 0.0))
        process = psutil.Process()
        cpu_times = process.cpu_times()
        cpu_time_seconds = float(cpu_times.user + cpu_times.system)
        rss_bytes = int(process.memory_info().rss)
        real_time_factor = (worker_ms / 1000) / max(signal.duration_seconds, 1e-6)
        return [
            _result(
                self,
                worker_ms,
                "ms",
                metadata={
                    "real_time_factor": real_time_factor,
                    "audio_duration_seconds": signal.duration_seconds,
                    "batch_size": 1,
                    "profile": context.profile_id,
                    "peak_process_rss_bytes": rss_bytes,
                    "process_cpu_time_seconds": cpu_time_seconds,
                    "time_to_first_audio_ms": item.metadata.get("time_to_first_audio_ms"),
                },
            )
        ]


PLUGINS = [AudioValidationPlugin(),DurationPlugin(),SilenceRatioPlugin(),ClippingPlugin(),LoudnessPlugin(),PitchProsodyPlugin(),SpeechRatePlugin(),TextNormalizationPlugin(),WerCerPlugin("wer"),WerCerPlugin("cer"),PerformancePlugin()]
