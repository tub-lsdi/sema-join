'use client';

import DataTable from './DataTable';
import { type BridgeTableEntry } from '@/lib/api';
import styles from './BridgeTablePanel.module.css';

interface Props {
  bridgeTable: BridgeTableEntry[];
  onCreateBridge: () => void;
  onPerformJoin: () => void;
  canCreate: boolean;
  canJoin: boolean;
  loading: boolean;
}

export default function BridgeTablePanel({
  bridgeTable,
  onCreateBridge,
  onPerformJoin,
  canCreate,
  canJoin,
  loading,
}: Props) {
  return (
    <div className={styles.panel}>
      {bridgeTable.length === 0 ? (
        <div className={styles.empty}>
          <h2 className={styles.title}>Create Bridge Table</h2>
          <p className={styles.description}>
            {!canCreate
              ? 'Upload files and select join columns to continue'
              : 'Ready to create bridge table'}
          </p>
          <button
            onClick={onCreateBridge}
            disabled={!canCreate || loading}
            className={styles.createButton}
          >
            {loading ? 'Creating...' : 'Create Bridge Table'}
          </button>
        </div>
      ) : (
        <>
          <div className={styles.header}>
            <h2 className={styles.title}>Bridge Table</h2>
            <button
              onClick={onCreateBridge}
              disabled={loading}
              className={styles.recreateButton}
            >
              {loading ? 'Recreating...' : 'Recreate'}
            </button>
          </div>

          <DataTable data={bridgeTable} />

          <button
            onClick={onPerformJoin}
            disabled={!canJoin || loading}
            className={styles.joinButton}
          >
            {loading ? 'Joining...' : 'Perform JOIN'}
          </button>
        </>
      )}
    </div>
  );
}

