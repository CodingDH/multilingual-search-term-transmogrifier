"""Compare generated candidate strings without inferring correctness."""

from __future__ import annotations

from typing import Dict, Optional

def categorize_difference(str1: str, str2: str, directionality: str = 'ltr') -> str:
	"""
	Categorize why two translation strings differ.

	Returns one of:
	  - 'identical': exact match
	  - 'capitalization': same text, different case (LTR scripts only)
	  - 'whitespace': same text ignoring whitespace
	  - 'both': differs in both capitalization and whitespace (LTR only)
	  - 'content': actual content difference

	RTL scripts (Arabic, Hebrew, etc.) skip capitalization checks since they
	typically have no case distinction.
	"""
	if str1 == str2:
		return 'identical'
	if directionality == 'ltr' and str1.lower() == str2.lower():
		return 'capitalization'
	if str1.strip().lower() == str2.strip().lower():
		if str1.strip() == str2.strip():
			return 'whitespace'
		return 'both' if directionality == 'ltr' else 'whitespace'
	return 'content'


def analyze_differences(
	service_values: Dict[str, Optional[str]],
	directionality: str = 'ltr',
) -> Dict[str, str]:
	"""
	Analyze all pairwise differences in a {key: translation} mapping.

	Returns a dict of pairwise difference types plus a 'summary' key with a
	comma-joined set of all difference types observed.
	"""
	actual = {k: v for k, v in service_values.items() if v is not None}
	if len(actual) <= 1:
		return {'summary': 'no_differences'}

	differences: Dict[str, str] = {}
	items = list(actual.items())
	for i, (k1, v1) in enumerate(items):
		for k2, v2 in items[i + 1:]:
			if v1 != v2:
				differences[f'{k1}_vs_{k2}'] = categorize_difference(v1, v2, directionality)

	if not differences:
		return {'summary': 'all_identical'}
	differences['summary'] = ','.join(sorted(set(differences.values())))
	return differences
