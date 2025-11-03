import styles from "./DataTable.module.css";

interface Props {
  data: Array<Record<string, any>>;
  highlightColumn?: string | null;
}

export default function DataTable({ data, highlightColumn }: Props) {
  if (!data || data.length === 0) return null;

  const columns = Object.keys(data[0]);
  const displayData = data.slice(0, 10);

  return (
    <div className={styles.container}>
      <table className={styles.table}>
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                className={
                  col === highlightColumn ? styles.highlightedHeader : undefined
                }
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {displayData.map((row, idx) => (
            <tr key={idx}>
              {columns.map((col) => (
                <td
                  key={col}
                  className={
                    col === highlightColumn ? styles.highlightedCell : undefined
                  }
                >
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
