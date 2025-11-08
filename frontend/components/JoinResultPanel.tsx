import DataTable from './DataTable';
import { type TableRow } from '@/lib/api';
import styles from './JoinResultPanel.module.css';

interface Props {
  data: TableRow[];
}

export default function JoinResultPanel({ data }: Props) {
  if (data.length === 0) {
    return null;
  }

  return (
    <div className={styles.panel}>
      <h2 className={styles.title}>Join Result</h2>
      <p className={styles.info}>
        {data.length} {data.length === 1 ? 'record' : 'records'} matched
      </p>
      <DataTable data={data} />
    </div>
  );
}
