import DataTable from './DataTable';
import styles from './JoinResultPanel.module.css';

interface Props {
  data: Array<Record<string, any>>;
}

export default function JoinResultPanel({ data }: Props) {
  if (data.length === 0) return null;

  return (
    <div className={styles.panel}>
      <h2 className={styles.title}>Join Result</h2>
      <DataTable data={data} />
    </div>
  );
}
