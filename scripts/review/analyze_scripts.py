"""Analyze Unicode scripts used by generated candidate terms."""

from __future__ import annotations

import functools
import unicodedata
from collections import Counter
from typing import Dict, List, Optional, Tuple

try:
    import regex as _regex

    # Single compiled alternation — one named group per script we care about.
    # Named groups become the return value directly; lru_cache keeps each
    # codepoint from being matched more than once per process.
    # Unicode property names: Han→CJK, Hiragana/Katakana→Japanese,
    # Hangul→Korean, Oriya→Odia (Unicode uses the old name).
    _SCRIPT_RE = _regex.compile(
        r'(?P<Latin>\p{Script=Latin})'
        r'|(?P<Cyrillic>\p{Script=Cyrillic})'
        r'|(?P<Arabic>\p{Script=Arabic})'
        r'|(?P<CJK>\p{Script=Han})'
        r'|(?P<Japanese>\p{Script=Hiragana}|\p{Script=Katakana})'
        r'|(?P<Korean>\p{Script=Hangul})'
        r'|(?P<Hebrew>\p{Script=Hebrew})'
        r'|(?P<Devanagari>\p{Script=Devanagari})'
        r'|(?P<Bengali>\p{Script=Bengali})'
        r'|(?P<Tamil>\p{Script=Tamil})'
        r'|(?P<Telugu>\p{Script=Telugu})'
        r'|(?P<Kannada>\p{Script=Kannada})'
        r'|(?P<Malayalam>\p{Script=Malayalam})'
        r'|(?P<Thai>\p{Script=Thai})'
        r'|(?P<Lao>\p{Script=Lao})'
        r'|(?P<Tibetan>\p{Script=Tibetan})'
        r'|(?P<Myanmar>\p{Script=Myanmar})'
        r'|(?P<Georgian>\p{Script=Georgian})'
        r'|(?P<Ethiopic>\p{Script=Ethiopic})'
        r'|(?P<Cherokee>\p{Script=Cherokee})'
        r'|(?P<Khmer>\p{Script=Khmer})'
        r'|(?P<Mongolian>\p{Script=Mongolian})'
        r'|(?P<Armenian>\p{Script=Armenian})'
        r'|(?P<Greek>\p{Script=Greek})'
        r'|(?P<Syriac>\p{Script=Syriac})'
        r'|(?P<Thaana>\p{Script=Thaana})'
        r'|(?P<Gujarati>\p{Script=Gujarati})'
        r'|(?P<Gurmukhi>\p{Script=Gurmukhi})'
        r'|(?P<Odia>\p{Script=Oriya})'
        r'|(?P<Sinhala>\p{Script=Sinhala})'
        r'|(?P<New_Tai_Lue>\p{Script=New_Tai_Lue})'
        r'|(?P<Tai_Le>\p{Script=Tai_Le})'
        r'|(?P<Tai_Tham>\p{Script=Tai_Tham})'
        r'|(?P<Tai_Viet>\p{Script=Tai_Viet})'
        r'|(?P<Balinese>\p{Script=Balinese})'
        r'|(?P<Sundanese>\p{Script=Sundanese})'
        r'|(?P<Javanese>\p{Script=Javanese})'
        r'|(?P<Cham>\p{Script=Cham})'
        r'|(?P<Yi>\p{Script=Yi})'
        r'|(?P<Lisu>\p{Script=Lisu})'
        r'|(?P<Miao>\p{Script=Miao})'
        r'|(?P<Vai>\p{Script=Vai})'
        r'|(?P<Bamum>\p{Script=Bamum})'
        r'|(?P<Nko>\p{Script=Nko})'
        r'|(?P<Tifinagh>\p{Script=Tifinagh})'
        r'|(?P<Coptic>\p{Script=Coptic})'
        r'|(?P<Adlam>\p{Script=Adlam})'
        r'|(?P<Osage>\p{Script=Osage})'
        r'|(?P<Buginese>\p{Script=Buginese})'
        r'|(?P<Samaritan>\p{Script=Samaritan})'
        r'|(?P<Mandaic>\p{Script=Mandaic})'
    )

    @functools.lru_cache(maxsize=4096)
    def char_script(cp: int) -> str:
        """Map a Unicode code point to a script family name."""
        m = _SCRIPT_RE.fullmatch(chr(cp))
        return m.lastgroup if m else 'Other'

except ImportError:
    def char_script(cp: int) -> str:
        """Map a Unicode code point to a script family name (range-based fallback)."""
        if (0x0041 <= cp <= 0x007A or 0x00C0 <= cp <= 0x024F
                or 0x0250 <= cp <= 0x02AF or 0x1E00 <= cp <= 0x1EFF):
            return 'Latin'
        if 0x0400 <= cp <= 0x052F:
            return 'Cyrillic'
        if 0x0600 <= cp <= 0x06FF or 0x0750 <= cp <= 0x077F or 0xFB50 <= cp <= 0xFDFF:
            return 'Arabic'
        if 0x0590 <= cp <= 0x05FF or 0xFB1D <= cp <= 0xFB4F:
            return 'Hebrew'
        if 0x0900 <= cp <= 0x097F:
            return 'Devanagari'
        if 0x0980 <= cp <= 0x09FF:
            return 'Bengali'
        if 0x0A80 <= cp <= 0x0AFF:
            return 'Gujarati'
        if 0x0B80 <= cp <= 0x0BFF:
            return 'Tamil'
        if 0x0C00 <= cp <= 0x0C7F:
            return 'Telugu'
        if 0x0C80 <= cp <= 0x0CFF:
            return 'Kannada'
        if 0x0D00 <= cp <= 0x0D7F:
            return 'Malayalam'
        if 0x0E00 <= cp <= 0x0E7F:
            return 'Thai'
        if 0x0E80 <= cp <= 0x0EFF:
            return 'Lao'
        if 0x0F00 <= cp <= 0x0FFF:
            return 'Tibetan'
        if 0x1000 <= cp <= 0x109F:
            return 'Myanmar'
        if 0x10A0 <= cp <= 0x10FF:
            return 'Georgian'
        if (0x1100 <= cp <= 0x11FF or 0x302E <= cp <= 0x302F
                or 0xA960 <= cp <= 0xA97F or 0xAC00 <= cp <= 0xD7FF):
            return 'Korean'
        if 0x1200 <= cp <= 0x137F or 0x2D80 <= cp <= 0x2DDF:
            return 'Ethiopic'
        if 0x13A0 <= cp <= 0x13FF:
            return 'Cherokee'
        if 0x1780 <= cp <= 0x17FF:
            return 'Khmer'
        if 0x1800 <= cp <= 0x18AF:
            return 'Mongolian'
        if 0x0530 <= cp <= 0x058F:
            return 'Armenian'
        if 0x0370 <= cp <= 0x03FF:
            return 'Greek'
        if 0x0700 <= cp <= 0x074F:
            return 'Syriac'
        if 0x0780 <= cp <= 0x07BF:
            return 'Thaana'
        if 0x0A00 <= cp <= 0x0A7F:
            return 'Gurmukhi'
        if 0x0B00 <= cp <= 0x0B7F:
            return 'Odia'
        if 0x0D80 <= cp <= 0x0DFF:
            return 'Sinhala'
        if (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF
                or 0x20000 <= cp <= 0x2A6DF or 0xF900 <= cp <= 0xFAFF):
            return 'CJK'
        if 0x3040 <= cp <= 0x30FF or 0x31F0 <= cp <= 0x31FF:
            return 'Japanese'
        return 'Other'


def detect_dominant_script(text: str) -> str:
	"""Return the dominant writing script of a translation string.

	Ignores spaces, punctuation, and digits — only letter/mark characters
	count toward the tally. Returns 'Unknown' for empty or punctuation-only
	strings.

	Examples
	--------
	>>> detect_dominant_script('Дигитална хуманистика')
	'Cyrillic'
	>>> detect_dominant_script('Digitalna humanistika')
	'Latin'
	>>> detect_dominant_script('الإنسانيات الرقمية')
	'Arabic'
	"""
	if not text or not isinstance(text, str):
		return 'Unknown'
	counts: Counter = Counter()
	for ch in text:
		cp = ord(ch)
		cat = unicodedata.category(ch)
		# Skip spaces, punctuation, digits, control chars
		if cat[0] in ('Z', 'P', 'S', 'C') or cat == 'Nd':
			continue
		counts[char_script(cp)] += 1
	if not counts:
		return 'Unknown'
	return counts.most_common(1)[0][0]


def detect_script_disagreement(
	translations: Dict[str, Optional[str]],
) -> Dict:
	"""Detect whether a set of translations uses more than one writing script.

	Useful for languages with digraphia (e.g. Serbian Cyrillic ↔ Latin,
	Uzbek, Azerbaijani) where the same term can be rendered in two scripts,
	inflating the apparent number of unique translations.

	Parameters
	----------
	translations : dict
		Mapping of service name → translation string (or None).

	Returns
	-------
	dict with keys:
		has_script_disagreement : bool
		scripts_found           : list of unique script names detected
		script_per_service      : list of (service, script) pairs
	"""
	valid = {s: t for s, t in translations.items()
			 if t and isinstance(t, str) and t.strip() and t not in ('nan', 'None')}
	if not valid:
		return {
			'has_script_disagreement': False,
			'scripts_found': [],
			'script_per_service': [],
		}

	per_service: List[Tuple[str, str]] = [
		(svc, detect_dominant_script(term)) for svc, term in valid.items()
	]
	unique_scripts: List[str] = sorted({s for _, s in per_service} - {'Unknown'})

	return {
		'has_script_disagreement': len(unique_scripts) > 1,
		'scripts_found': unique_scripts,
		'script_per_service': per_service,
	}
