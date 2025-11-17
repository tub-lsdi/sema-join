import Link from "next/link";
import styles from "./Header.module.css";

export default function Header() {
  return (
    <>
      <div className={styles.container}>
        <h1 className={styles.title}>
          SEMA-JOIN: Joining Semantically-Related Tables
        </h1>
        <Link href="/" className={styles.logoContainer}>
          <img src="/d2ip_logo.png" alt="D2IP Logo" className={styles.logo} />
        </Link>
      </div>

      {/* Informative explanation box */}
      <div className={styles.infoBox}>
        <div className={styles.infoHeader}>
          <strong>Semantic Join: Overview</strong>
        </div>
        <p className={styles.infoText}>
          Traditional relational joins require exact string matching between key
          columns. Semantic join extends this by leveraging statistical
          co-occurrence patterns derived from large table corpora to identify
          semantically equivalent values across different representations. This
          enables joins between columns with different encoding standards (e.g.,
          country names ↔ country codes).
        </p>
        <div className={styles.algorithmBox}>
          <p className={styles.algorithmText}>
            Semantic relatedness is quantified through Normalized Pointwise
            Mutual Information (NPMI) scores, computed from corpus co-occurrence
            statistics. Two complementary algorithms are provided: RS-JP offers
            a fast baseline through independent per-row matching, while CS-JP-LP
            employs Linear Programming to formulate the join prediction as a
            global optimization problem, ensuring consistent mappings across the
            entire dataset with improved accuracy.
          </p>
        </div>
        <div className={styles.infoPaper}>
          <strong>Reference:</strong> He et al., "SEMA-JOIN: Joining
          Semantically-Related Tables Using Big Table Corpora"
          <em>Proceedings of the VLDB Endowment</em>, Vol. 8, No. 12, 2015
        </div>
      </div>
    </>
  );
}
