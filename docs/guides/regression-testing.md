# Regression testing

Regression gates are scheduled for Phase 4 because they must operate on real aggregate metrics, not static dashboard examples.

## Intended policy shape

```yaml
metric: wer
operator: less_than_or_equal
threshold: 0.03
comparison: relative_increase
severity: fail
filters:
  language: en
  tags: [narration]
```

## Directionality

- Lower is better: WER, CER, clipping ratio, latency, real-time factor.
- Higher is better: speaker similarity when the plugin is available.
- Target-range metrics: loudness and expected-duration deviation.

A policy result will record baseline value, observed value, normalized delta, affected sample count, decision, and an explanation. Policies will never claim pass/fail when the required metric was unavailable.
