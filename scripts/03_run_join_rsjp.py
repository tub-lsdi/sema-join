from loguru import logger
from sema_join.joiner import rs_jp_join
import pprint

def main():
    logger.info("Testing RS-JP Join...")

    R = ["barcelona", "real madrid", "arsenal", "bayern munich"]
    S = ["esp", "eng", "ita", "deu"]

    # Normalize inputs just like corpus data
    R_norm = [v.strip().lower() for v in R]
    S_norm = [v.strip().lower() for v in S]

    join_map = rs_jp_join(R_norm, S_norm)

    logger.info("Join results (Normalized):")
    pprint.pprint(join_map)

    # "denormalized" map for display
    norm_to_orig_r = dict(zip(R_norm, R))
    norm_to_orig_s = dict(zip(S_norm, S))

    final_join = {
        norm_to_orig_r[r_norm]: norm_to_orig_s.get(s_norm)
        for r_norm, s_norm in join_map.items()
    }

    logger.info("\nJoin results (Original Strings):")
    pprint.pprint(final_join)


if __name__ == "__main__":
    main()