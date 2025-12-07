import DataTable from "./DataTable";
import { type TableRow, type JoinMethod } from "@/lib/api";
import styles from "./JoinResultPanel.module.css";

interface Props {
  data: TableRow[];
  joinMethod?: JoinMethod;
  onViewFullTable?: () => void;
}

export default function JoinResultPanel({ data, joinMethod, onViewFullTable }: Props) {
  if (data.length === 0) {
    return null;
  }

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>Join Result</h2>
          <p className={styles.info}>
            {data.length} {data.length === 1 ? "record" : "records"} matched
          </p>
        </div>
        {data.length > 10 && onViewFullTable && (
          <button
            className={styles.viewFullButton}
            onClick={onViewFullTable}
          >
            View Full Table
          </button>
        )}
      </div>
      <DataTable data={data} joinMethod={joinMethod} />
    </div>
  );
}
