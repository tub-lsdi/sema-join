"use client";

import { type TableRow } from "@/lib/api";
import styles from "./InteractiveDataTable.module.css";

interface Props {
  data: TableRow[];
  selectedColumn?: string;
  onColumnSelect?: (column: string) => void;
}

export default function InteractiveDataTable({
  data,
  selectedColumn,
  onColumnSelect,
}: Props) {
  if (!data || data.length === 0) return null;

  const columns = Array.from(
    new Set(data.flatMap((row) => Object.keys(row || {})))
  );
  const minRows = 5;

  // Pad with empty rows
  const displayData = [...data];
  while (displayData.length < minRows) {
    displayData.push(columns.reduce((acc, col) => ({ ...acc, [col]: "" }), {}));
  }

  return (
    <div className={styles.container}>
      <table className={styles.table}>
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                onClick={() => onColumnSelect?.(col)}
                className={
                  selectedColumn === col ? styles.selected : styles.clickable
                }
              >
                {selectedColumn === col && <span>✓ </span>}
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {displayData.slice(0, minRows).map((row, idx) => {
            const isEmpty = idx >= data.length;
            return (
              <tr key={idx} className={isEmpty ? styles.empty : ""}>
                {columns.map((col) => (
                  <td
                    key={col}
                    className={selectedColumn === col ? styles.highlighted : ""}
                  >
                    {isEmpty
                      ? "—"
                      : typeof row[col] === "object"
                      ? JSON.stringify(row[col])
                      : String(row[col] ?? "")}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
