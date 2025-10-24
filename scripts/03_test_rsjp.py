from time import sleep

from loguru import logger

from sema_join.corpus import (
    normalize_value,
    set_normalization_strategy,
    NormalizationStrategy,
)
from sema_join.joiner import rs_jp_join
import pprint

countries = [
    "Germany",
    "Australia",
    "United Kingdom",
    "Switzerland",
    "South Korea",
    "Sri Lanka",
    "Latvia",
    "Belize",
]

# The "right side" data sources (Lists S)
fips_codes = [
    ("Germany", "GM"),
    ("Australia", "AS"),
    ("United Kingdom", "UK"),
    ("Switzerland", "SZ"),
    ("South Korea", "KS"),
    ("Sri Lanka", "CE"),
    ("Latvia", "LG"),
    ("Belize", "BH"),
]

iso_codes = [
    ("Germany", "DE"),
    ("Australia", "AU"),
    ("United Kingdom", "GB"),
    ("Switzerland", "CH"),
    ("South Korea", "KR"),
    ("Sri Lanka", "LK"),
    ("Latvia", "LV"),
    ("Belize", "BZ"),
]

mixed_incomplete_codes = [
    ("Germany", "GM"),  # FIPS code
    ("Australia", "AU"),  # ISO code
    ("Switzerland", "CH"),  # ISO code
    ("South Korea", "KS"),  # FIPS code
    ("Latvia", "LV"),  # ISO code
    ("Belize", "BH"),  # FIPS code
]


def test_rsjp_join(
    left_values: list[str], right_values: list[tuple[str, str]], description: str
):
    logger.info(f"\n--- Testing RS-JP Join: {description} ---")
    r_norm = [normalize_value(v[1]) for v in right_values]
    l_norm = [normalize_value(v) for v in left_values]

    join_map: dict[str, str | None] = rs_jp_join(r_norm, l_norm)

    pprint.pprint({k: join_map[k] for k in sorted(join_map)})
    sleep(0.1)


def main():
    logger.info("Testing RS-JP Join...")
    # Normalize inputs just like corpus data
    set_normalization_strategy(NormalizationStrategy.ALPHANUMERIC_STRICT)
    test_rsjp_join(countries, fips_codes, "FIPS Codes")
    test_rsjp_join(countries, iso_codes, "ISO Codes")
    test_rsjp_join(countries, mixed_incomplete_codes, "Mixed Incomplete Codes")


if __name__ == "__main__":
    main()
