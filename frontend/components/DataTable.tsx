"use client";

import styles from "./DataTable.module.css";

interface Props {
  data: Array<Record<string, any>>;
}

export default function DataTable({ data }: Props) {
  if (!data || data.length === 0) return null;

  const columns = Array.from(
    new Set(data.flatMap((row) => Object.keys(row || {})))
  );
  const displayData = data.slice(0, 10);

  return (
    <div className={styles.container}>
      <table className={styles.table}>
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {displayData.map((row, idx) => (
            <tr key={idx}>
              {columns.map((col) => (
                <td key={col}>
                  {typeof row[col] === "object"
                    ? JSON.stringify(row[col])
                    : String(row[col] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length > 10 && (
        <p className={styles.more}>Showing 10 of {data.length} rows</p>
      )}
    </div>
  );
}
