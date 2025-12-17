import csv
import io
from typing import List, Dict, Any


def parse_csv_to_list_of_dicts(csv_content: str) -> List[Dict[str, Any]]:
    if not csv_content or not csv_content.strip():
        raise ValueError("CSV content is empty")

    try:
        csv_file = io.StringIO(csv_content)

        # Try to detect dialect, fallback to default
        try:
            dialect = csv.Sniffer().sniff(csv_content[:1024])
            csv_file.seek(0)
            reader = csv.DictReader(csv_file, dialect=dialect)
        except csv.Error:
            csv_file.seek(0)
            reader = csv.DictReader(csv_file)

        rows = []
        for row in reader:
            if any(v and v.strip() for v in row.values() if v):
                processed = {key: _convert_value(value) for key, value in row.items()}
                rows.append(processed)

        if not rows:
            raise ValueError("CSV contains no valid data rows")

        return rows

    except csv.Error as e:
        raise ValueError(f"Invalid CSV format: {e}") from e
    except Exception as e:
        raise ValueError(f"Error parsing CSV: {e}") from e


def _convert_value(value: str) -> Any:
    """Convert string value to appropriate type (int, float, or str)."""
    if not value or not value.strip():
        return None

    value = value.strip()

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    return value
