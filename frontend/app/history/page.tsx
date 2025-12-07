"use client";

import { useEffect, useState } from "react";
import Header from "@/components/Header";
import HistoryTable from "./components/HistoryTable";
import styles from "./page.module.css";
import { fetchHistory } from "@/lib/api";

export default function HistoryPage() {
  const [entries, setEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadHistory() {
      try {
        const resp = await fetchHistory();
        setEntries(resp.entries || []);
      } catch (e) {
        console.error("Failed to load history:", e);
        setEntries([]);
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, []);

  return (
    <div className={styles.container}>
      <div className={styles.wrapper}>
        <Header />

        <div className={styles.card}>
          <div style={{ width: "100%" }}>
            <h2 style={{ margin: 0, marginBottom: "0.75rem" }}>History</h2>
            {loading ? (
              <p>Loading...</p>
            ) : (
              <HistoryTable data={entries} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
