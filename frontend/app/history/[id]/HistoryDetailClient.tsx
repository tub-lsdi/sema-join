"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Header from "@/components/Header";
import DataTable from "@/components/DataTable";
import TableModal from "@/components/TableModal";
import styles from "../page.module.css";
import { fetchHistoryDetail, type HistoryDetailResponse, type TableRow } from "@/lib/api";

export default function HistoryDetailClient() {
  const params = useParams();
  const idStr = params?.id;
  const id = idStr ? Number(idStr) : NaN;

  const [entry, setEntry] = useState<HistoryDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalData, setModalData] = useState<{ title: string; data: TableRow[]; selectedColumn?: string } | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      if (!idStr || Number.isNaN(id)) {
        setError("Invalid history id");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const resp = await fetchHistoryDetail(Number(id));
        if (!mounted) return;
        setEntry(resp);
      } catch (e) {
        if (!mounted) return;
        const errorMessage = e instanceof Error ? e.message : "Failed to load history";
        setError(errorMessage);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    load();
    return () => {
      mounted = false;
    };
  }, [idStr]);

  const handleViewFullTable = (title: string, data: TableRow[], selectedColumn?: string) => {
    setModalData({ title, data, selectedColumn });
    setModalOpen(true);
  };

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.wrapper}>
          <Header />
          <div className={styles.card}>Loading...</div>
        </div>
      </div>
    );
  }

  if (error || !entry) {
    return (
      <div className={styles.container}>
        <div className={styles.wrapper}>
          <Header />
          <div className={styles.card}>{error || "No history found."}</div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.wrapper}>
        <Header />

        <div className={styles.card}>
          <h2 className={styles.title}>
            History #{entry.id} — {new Date(entry.timestamp).toLocaleString()}
          </h2>
        </div>

        <div className={styles.stack}>
          <div className={styles.gridTwoCols}>
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <h3 className={styles.sectionTitle}>List R</h3>
                {entry.list_r && entry.list_r.length > 10 && (
                  <button
                    className={styles.viewFullButton}
                    onClick={() => handleViewFullTable("List R", entry.list_r, entry.r_join_col || undefined)}
                  >
                    View Full Table
                  </button>
                )}
              </div>
              <DataTable
                data={entry.list_r || []}
                highlightColumn={entry.r_join_col}
              />
            </div>

            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <h3 className={styles.sectionTitle}>List S</h3>
                {entry.list_s && entry.list_s.length > 10 && (
                  <button
                    className={styles.viewFullButton}
                    onClick={() => handleViewFullTable("List S", entry.list_s, entry.s_join_col || undefined)}
                  >
                    View Full Table
                  </button>
                )}
              </div>
              <DataTable
                data={entry.list_s || []}
                highlightColumn={entry.s_join_col}
              />
            </div>
          </div>

          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <h3 className={styles.sectionTitle}>Bridge Table</h3>
              {entry.bridge_table && entry.bridge_table.length > 10 && (
                <button
                  className={styles.viewFullButton}
                  onClick={() => handleViewFullTable("Bridge Table", entry.bridge_table)}
                >
                  View Full Table
                </button>
              )}
            </div>
            <DataTable data={entry.bridge_table || []} />
          </div>

          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <h3 className={styles.sectionTitle}>Result</h3>
              {entry.result && entry.result.length > 10 && (
                <button
                  className={styles.viewFullButton}
                  onClick={() => handleViewFullTable("Result", entry.result)}
                >
                  View Full Table
                </button>
              )}
            </div>
            <DataTable data={entry.result || []} />
          </div>
        </div>
      </div>

      {modalOpen && modalData && (
        <TableModal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title={modalData.title}
          data={modalData.data}
          selectedColumn={modalData.selectedColumn}
        />
      )}
    </div>
  );
}
