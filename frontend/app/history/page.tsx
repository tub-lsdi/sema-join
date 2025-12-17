"use client";

import { useEffect, useState } from "react";
import Header from "@/components/Header";
import HistoryTable from "./components/HistoryTable";
import styles from "./page.module.css";
import { fetchHistory, type HistoryEntry } from "@/lib/api";
import ErrorAlert from "@/components/ErrorAlert";

export default function HistoryPage() {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    async function loadHistory() {
      try {
        const resp = await fetchHistory();
        setEntries(resp.entries || []);
      } catch (e) {
        const errorMessage =
          e instanceof Error ? e.message : "Failed to load history";
        setError(errorMessage);
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
          <div className={styles.content}>
            <h2 className={styles.heading}>History</h2>
            {error && <ErrorAlert message={error} />}
            {loading ? <p>Loading...</p> : <HistoryTable data={entries} />}
          </div>
        </div>
      </div>
    </div>
  );
}
