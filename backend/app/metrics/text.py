from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    raw: str
    normalized: str
    tokens: list[str]
    trace: list[str]


def normalize_text(text: str, language: str) -> NormalizationResult:
    trace: list[str] = ["unicode_nfc"]
    value = unicodedata.normalize("NFC", text)
    value = re.sub(r"\s+", " ", value).strip()
    trace.append("whitespace")
    if language.lower().startswith(("en", "es")):
        value = value.lower()
        trace.append("casefold")
    punctuation = r"[\.,;:!؟?،\-—–\"'`()\[\]{}]"
    value = re.sub(punctuation, " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    trace.append("punctuation")
    if language.lower().startswith(("zh", "ja", "ko")):
        tokens = [char for char in value if not char.isspace()]
        trace.append("character_tokenizer")
    else:
        tokens = value.split() if value else []
        trace.append("whitespace_tokenizer")
    return NormalizationResult(raw=text, normalized=value, tokens=tokens, trace=trace)


def levenshtein_alignment(reference: list[str], hypothesis: list[str]) -> tuple[int, int, int, int, list[dict[str, str]]]:
    rows, cols = len(reference) + 1, len(hypothesis) + 1
    dp = [[0] * cols for _ in range(rows)]
    for i in range(rows): dp[i][0] = i
    for j in range(cols): dp[0][j] = j
    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if reference[i - 1] == hypothesis[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    i, j = len(reference), len(hypothesis)
    insertion = deletion = substitution = 0
    alignment: list[dict[str, str]] = []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] and reference[i - 1] == hypothesis[j - 1]:
            alignment.append({"op": "equal", "reference": reference[i - 1], "hypothesis": hypothesis[j - 1]}); i -= 1; j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            alignment.append({"op": "substitution", "reference": reference[i - 1], "hypothesis": hypothesis[j - 1]}); substitution += 1; i -= 1; j -= 1
        elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
            alignment.append({"op": "insertion", "reference": "", "hypothesis": hypothesis[j - 1]}); insertion += 1; j -= 1
        else:
            alignment.append({"op": "deletion", "reference": reference[i - 1], "hypothesis": ""}); deletion += 1; i -= 1
    alignment.reverse()
    return insertion, deletion, substitution, dp[-1][-1], alignment
