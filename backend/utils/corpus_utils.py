"""
Corpus data processing utilities for WDC table parsing.
"""
import json
import hashlib
from typing import Iterator, Any
from loguru import logger

from backend.utils.normalization import NormalizationStrategy


class CorpusParser:
    """Utility class for parsing and processing corpus tables."""
    
    def __init__(self, strategy: NormalizationStrategy = NormalizationStrategy.ALPHANUMERIC_LOOSE):
        """
        Initialize the corpus parser.
        
        Args:
            strategy: Normalization strategy to use
        """
        self.strategy = strategy
        logger.info(f"Initialized CorpusParser with strategy: {strategy.name}")
    
    def set_strategy(self, strategy: NormalizationStrategy):
        """
        Set the normalization strategy.
        
        Args:
            strategy: New normalization strategy
        """
        self.strategy = strategy
        logger.info(f"Changed normalization strategy to: {strategy.name}")
    
    def normalize_value(self, v: Any) -> str:
        """
        Normalize a value using the current strategy.
        
        Args:
            v: Value to normalize
            
        Returns:
            Normalized string value
        """
        return self.strategy.normalize(v)
    
    def extract_rows_from_wdc_dict(self, table: dict[str, Any]) -> list[list[str]]:
        """
        Extract and normalize rows from WDC-style table JSON.
        
        Args:
            table: WDC format table dictionary
            
        Returns:
            List of normalized rows
        """
        relation = table.get("relation", [])
        if not relation or not isinstance(relation, list):
            logger.warning(f"Table relation {relation} not found or empty.")
            return []

        # Transpose if vertical
        if table.get("tableOrientation", "").upper() == "VERTICAL":
            try:
                relation = list(zip(*relation))
            except TypeError:
                logger.error("Failed to transpose table rows; invalid structure.")
                return []

        rows = relation

        # Skip header row if detected
        if table.get("hasHeader", False):
            header_idx = table.get("headerRowIndex")
            if header_idx is not None and 0 <= header_idx < len(rows):
                rows = [r for i, r in enumerate(rows) if i != header_idx]
            else:
                logger.warning(
                    f"Table headerRowIndex {header_idx} not found, even though hasHeader is 'true'. Skipping table."
                )
                return []

        # Normalize and clean
        normalized = []
        for row in rows:
            cleaned = []
            for x in row:
                if x is not None:
                    value = self.normalize_value(x)
                    if value:
                        cleaned.append(value)
            if cleaned:
                normalized.append(cleaned)
        return normalized
    
    def stream_json_tables(self, path: str) -> Iterator[dict[str, Any]]:
        """
        Generator yielding parsed JSON tables from an NDJSON file.
        
        Args:
            path: Path to NDJSON file
            
        Yields:
            Parsed table dictionaries
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
    
    @staticmethod
    def table_hash(rows: list[list[str]]) -> str:
        """
        Compute a stable hash for a table given normalized rows.
        
        Args:
            rows: Normalized rows from extract_rows_from_wdc_dict
            
        Returns:
            SHA1 hash of the table
        """
        normalized_json = json.dumps(rows, separators=(",", ":"), sort_keys=True)
        return hashlib.sha1(normalized_json.encode("utf-8")).hexdigest()


# Global instance for convenience
_default_parser = CorpusParser()


def set_corpus_strategy(strategy: NormalizationStrategy):
    """
    Set the normalization strategy for the global parser.
    
    Convenience function for backward compatibility.
    """
    _default_parser.set_strategy(strategy)


def extract_rows_from_wdc_dict(table: dict[str, Any]) -> list[list[str]]:
    """
    Extract rows from WDC-style table JSON using global parser.
    
    Convenience function for backward compatibility.
    """
    return _default_parser.extract_rows_from_wdc_dict(table)


def stream_json_tables(path: str) -> Iterator[dict[str, Any]]:
    """
    Stream JSON tables from file using global parser.
    
    Convenience function for backward compatibility.
    """
    return _default_parser.stream_json_tables(path)


def table_hash(rows: list[list[str]]) -> str:
    """
    Compute table hash.
    
    Convenience function for backward compatibility.
    """
    return CorpusParser.table_hash(rows)

