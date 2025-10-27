"use client";

import DataTable from "./DataTable";
import { type BridgeTableEntry, type JoinMethod } from "@/lib/api";
import styles from "./BridgeTablePanel.module.css";

interface Props {
  bridgeTable: BridgeTableEntry[];
  joinMethod: JoinMethod;
  onJoinMethodChange: (method: JoinMethod) => void;
  onCreateBridge: () => void;
  onPerformJoin: () => void;
  canCreate: boolean;
  canJoin: boolean;
  loading: boolean;
}

export default function BridgeTablePanel({
  bridgeTable,
  joinMethod,
  onJoinMethodChange,
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
              ? "Upload files and select join columns to continue"
              : "Ready to create bridge table"}
          </p>

          <div className={styles.joinMethodSelector}>
            <label htmlFor="join-method" className={styles.label}>
              Join Algorithm:
            </label>
            <select
              id="join-method"
              value={joinMethod}
              onChange={(e) => onJoinMethodChange(e.target.value as JoinMethod)}
              disabled={loading}
              className={styles.select}
            >
              <option value="row">RS-JP (Row-based)</option>
              <option value="column">CS-JP-LP (Column-based)</option>
            </select>
          </div>

          <button
            onClick={onCreateBridge}
            disabled={!canCreate || loading}
            className={styles.createButton}
          >
            {loading ? "Creating..." : "Create Bridge Table"}
          </button>
        </div>
      ) : (
        <>
          <div className={styles.header}>
            <h2 className={styles.title}>
              Bridge Table ({bridgeTable.length} matches)
            </h2>
            <div className={styles.headerControls}>
              <select
                id="join-method-recreate"
                value={joinMethod}
                onChange={(e) =>
                  onJoinMethodChange(e.target.value as JoinMethod)
                }
                disabled={loading}
                className={styles.selectCompact}
              >
                <option value="row">RS-JP (Greedy)</option>
                <option value="column">CS-JP-LP (Optimal)</option>
              </select>
              <button
                onClick={onCreateBridge}
                disabled={loading}
                className={styles.recreateButton}
              >
                {loading ? "Recreating..." : "Recreate"}
              </button>
            </div>
          </div>

          <DataTable data={bridgeTable} />

          <button
            onClick={onPerformJoin}
            disabled={!canJoin || loading}
            className={styles.joinButton}
          >
            {loading ? "Joining..." : "Perform JOIN"}
          </button>
        </>
      )}
    </div>
  );
}
