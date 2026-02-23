"""
Compatibility shim for older imports.

The real implementation now lives under the nlp/ package to keep concerns
modular and easily testable. Existing imports of
`from nlp_parser import parse_voice_command` continue to work.
"""

from __future__ import annotations

from typing import Optional

from nlp import detect_language as _detect_language
from nlp import parse_voice_command as _parse_voice_command
from schemas import ParsedVoiceCommand


def detect_language(text: str, hint: Optional[str] = None) -> str:  # pragma: no cover - thin wrapper
    return _detect_language(text, hint)


def parse_voice_command(text: str, language_hint: Optional[str] = None) -> ParsedVoiceCommand:  # pragma: no cover - thin wrapper
    return _parse_voice_command(text, language_hint)
