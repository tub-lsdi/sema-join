import Header from "@/components/Header";
import HistoryTable from "./components/HistoryTable";
import styles from "./page.module.css";
import { fetchHistory } from "@/lib/api";

export default async function HistoryPage() {
  let entries: any[] = [];

  try {
    const resp = await fetchHistory();
    entries = resp.entries || [];
  } catch (e) {
    // swallow errors and show empty history
    entries = [];
  }

  return (
    <div className={styles.container}>
      <div className={styles.wrapper}>
        <Header />

        <div className={styles.card}>
          <div style={{ width: "100%" }}>
            <h2 style={{ margin: 0, marginBottom: "0.75rem" }}>History</h2>
            <HistoryTable data={entries} />
          </div>
        </div>
      </div>
    </div>
  );
}
