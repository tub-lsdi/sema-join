import Link from "next/link";
import styles from "./Header.module.css";

export default function Header() {
  return (
    <div className={styles.container}>
      <Link href="/">
        <h1 className={styles.title}>
          SEMA-JOIN: Joining Semantically-Related Tables
        </h1>
      </Link>
      <div className={styles.logoContainer}>
        <img src="/d2ip_logo.png" alt="D2IP Logo" className={styles.logo} />
      </div>
    </div>
  );
}
