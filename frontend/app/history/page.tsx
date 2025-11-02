import Header from "@/components/Header";
import HistoryTable from "./components/HistoryTable";
import styles from "./page.module.css";

export default function HistoryPage() {
  return (
    <div className={styles.container}>
      <div className={styles.wrapper}>
        <Header />

        <div className={styles.card}>
          <div style={{ width: "100%" }}>
            <h2 style={{ margin: 0, marginBottom: "0.75rem" }}>History</h2>
            <HistoryTable data={[]} />
          </div>
        </div>
      </div>
    </div>
  );
}
