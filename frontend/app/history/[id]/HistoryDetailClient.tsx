"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Header from "@/components/Header";
import DataTable from "@/components/DataTable";
import TableModal from "@/components/TableModal";
import styles from "../page.module.css";
import { fetchHistoryDetail } from "@/lib/api";

export default function HistoryDetailClient() {
  const params = useParams();
  const idStr = params?.id;
  const id = idStr ? Number(idStr) : NaN;

  const [entry, setEntry] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalData, setModalData] = useState<any[]>([]);
  const [modalTitle, setModalTitle] = useState("");
  const [modalHighlightColumn, setModalHighlightColumn] = useState<string | undefined>(undefined);

  const openModal = (title: string, data: any[], highlightColumn?: string) => {
    setModalTitle(title);
    setModalData(data);
    setModalHighlightColumn(highlightColumn);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setModalData([]);
    setModalTitle("");
    setModalHighlightColumn(undefined);
  };

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
        setEntry(resp as any);
      } catch (e: any) {
        if (!mounted) return;
        setError(e?.message || "Failed to load history");
      } finally {
        if (mounted) setLoading(false);
      }
    }

    load();
    return () => {
      mounted = false;
    };
  }, [idStr]);

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
                <button
                  onClick={() => openModal("List R", entry.list_r || [], entry.r_join_col)}
                  className={styles.viewButton}
                >
                  View Full Table
                </button>
              </div>
              <DataTable
                data={entry.list_r || []}
                highlightColumn={entry.r_join_col}
              />
            </div>

            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <h3 className={styles.sectionTitle}>List S</h3>
                <button
                  onClick={() => openModal("List S", entry.list_s || [], entry.s_join_col)}
                  className={styles.viewButton}
                >
                  View Full Table
                </button>
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
              <button
                onClick={() => openModal("Bridge Table", entry.bridge_table || [])}
                className={styles.viewButton}
              >
                View Full Table
              </button>
            </div>
            <DataTable data={entry.bridge_table || []} />
          </div>

          <div className={styles.card}>
            <div className={styles.cardHeader}>
              <h3 className={styles.sectionTitle}>Result</h3>
              <button
                onClick={() => openModal("Result", entry.result || [])}
                className={styles.viewButton}
              >
                View Full Table
              </button>
            </div>
            <DataTable data={entry.result || []} />
          </div>
        </div>

        <TableModal
          isOpen={modalOpen}
          onClose={closeModal}
          title={modalTitle}
          data={modalData}
          selectedColumn={modalHighlightColumn}
        />
      </div>
    </div>
  );
}
