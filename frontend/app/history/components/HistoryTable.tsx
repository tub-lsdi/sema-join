import styles from "./HistoryTable.module.css";

interface HistoryTableEntry {
  id: number;
  timestamp: string;
  r_join_col: string;
  s_join_col: string;
}

interface Props {
  data: Array<HistoryTableEntry>;
}

export default function HistoryTable({ data }: Props) {
  const columns = ["Timestamp", "R Join Column", "S Join Column"];

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
          {data.map((entry) => (
            <tr key={entry.timestamp}>
              <td>{new Date(entry.timestamp).toLocaleString()}</td>
              <td>{entry.r_join_col}</td>
              <td>{entry.s_join_col}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
