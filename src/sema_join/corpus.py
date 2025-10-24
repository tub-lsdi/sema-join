import re
import json
import hashlib
from enum import Enum
from typing import Iterator, Any
import regex as re_unicode

from loguru import logger

# Pre-compile regex for efficiency
class NormalizationStrategy(Enum):
    """
    Defines the available normalization strategies.
    The value of each member is the compiled regex pattern.
    """

    ALPHANUMERIC_STRICT = re.compile(r'[^a-z0-9]+')
    """Only allows basic a-z and 0-9. (Fastest)"""

    UNICODE_WORDS = re.compile(r'[^\w]+')
    """Allows Unicode letters, numbers, and underscores."""

    ALPHANUMERIC_LOOSE = re_unicode.compile(r'[^\p{L}\p{N}]+', re_unicode.UNICODE)
    """Allows only Unicode letters and numbers. (Recommended)"""

    def normalize(self, v: Any) -> str:
        """Helper method to normalize a value using this strategy."""
        if not isinstance(v, str):
            v = str(v)
        v = v.strip().lower()
        # self.value is the compiled regex
        v = self.value.sub(' ', v)
        return v.strip()

_CURRENT_STRATEGY = NormalizationStrategy.ALPHANUMERIC_LOOSE

def set_normalization_strategy(strategy: NormalizationStrategy):
    """
    Globally sets the normalization strategy for all subsequent calls.
    """
    global _CURRENT_STRATEGY
    logger.info(f"Setting normalization strategy to: {strategy.name}")
    _CURRENT_STRATEGY = strategy

def normalize_value(v: Any) -> str:
    """
    Lowercase, alphanumeric normalization for cell values
    using the currently active global strategy.
    """
    return _CURRENT_STRATEGY.normalize(v)

def extract_rows_from_wdc_dict(table: dict[str, Any]) -> list[list[str]]:
    """Extract rows from WDC-style table JSON."""
    relation = table.get('relation', [])
    if not relation or not isinstance(relation, list):
        logger.warning(f'Table relation {relation} not found or empty.')
        return []

    # Transpose if horizontal
    if table.get('tableOrientation', '').upper() == 'HORIZONTAL':
        try:
            relation = list(zip(*relation))
        except TypeError:
            logger.error("Failed to transpose table rows; invalid structure.")
            return []

    rows = relation

    # Skip header row if detected
    if table.get('hasHeader', False):
        header_idx = table.get('headerRowIndex', 0)
        if 0 <= header_idx < len(rows):
            rows = [r for i, r in enumerate(rows) if i != header_idx]

    # Normalize and clean
    normalized = []
    for row in rows:
        cleaned = []
        for x in row:
            if x is not None:
                value = normalize_value(x)
                if value:
                    cleaned.append(value)
        if cleaned:
            normalized.append(cleaned)
    return normalized

def stream_json_tables(path: str) -> Iterator[dict[str, Any]]:
    """
    Generator yielding parsed JSON tables from an NDJSON file.
    Uses UTF-8 but replaces any invalid characters.
    """
    try:
        # Use utf-8 but replace errors instead of crashing.
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue  # skip malformed JSON lines

    except Exception as e:
        # This would now only catch non-decoding errors (e.g., permissions)
        logger.error(f"Could not read {path}: {e}")

def table_hash(rows: list[list[str]]) -> str:
    """
    Compute a stable hash for a table given normalized rows.
    Rows should already be cleaned via extract_rows_from_dict().
    """
    normalized_json = json.dumps(rows, separators=(',', ':'), sort_keys=True)
    return hashlib.sha1(normalized_json.encode("utf-8")).hexdigest()