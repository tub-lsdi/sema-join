import { type JoinMethod } from "@/lib/api";
import { getScoreColumnConfig } from "@/lib/utils";
import styles from "./DataTable.module.css";

interface Props {
  data: Array<Record<string, any>>;
  highlightColumn?: string | null;
  joinMethod?: JoinMethod;
  showAll?: boolean;
}

export default function DataTable({
  data,
  highlightColumn,
  joinMethod,
  showAll,
}: Props) {
  if (!data || data.length === 0) return null;

  const columns = Array.from(
    new Set(data.flatMap((row) => Object.keys(row || {})))
  );
  const displayData = showAll ? data : data.slice(0, 10);

  // Get score column configuration based on the algorithm that was used
  const scoreColumn = getScoreColumnConfig(joinMethod);

  // Map column names based on join method
  const getColumnDisplayName = (col: string): string => {
    if (col === "npmi") {
      return scoreColumn.label;
    }
    return col;
  };

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
                {getColumnDisplayName(col)}
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
      {!showAll && data.length > 10 && (
        <p className={styles.more}>Showing 10 of {data.length} rows</p>
      )}
    </div>
  );
}
