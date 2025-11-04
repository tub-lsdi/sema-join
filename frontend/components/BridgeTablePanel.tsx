"use client";

import DataTable from "./DataTable";
import { type BridgeTableEntry, type JoinMethod } from "@/lib/api";
import styles from "./BridgeTablePanel.module.css";

interface Props {
  bridgeTable: BridgeTableEntry[];
  joinMethod: JoinMethod;
  topK: number;
  selectedEntries: Set<number>;
  onJoinMethodChange: (method: JoinMethod) => void;
  onTopKChange: (topK: number) => void;
  onCreateBridge: () => void;
  onPerformJoin: () => void;
  onToggleEntry: (index: number) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  canCreate: boolean;
  canJoin: boolean;
  loading: boolean;
}

export default function BridgeTablePanel({
  bridgeTable,
  joinMethod,
  topK,
  selectedEntries,
  onJoinMethodChange,
  onTopKChange,
  onCreateBridge,
  onPerformJoin,
  onToggleEntry,
  onSelectAll,
  onDeselectAll,
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
              <option value="row">RS-JP</option>
              <option value="column">CS-JP-LP</option>
            </select>
          </div>

          <div className={styles.joinMethodSelector}>
            <label htmlFor="top-k" className={styles.label}>
              Top K Matches:
            </label>
            <input
              id="top-k"
              type="number"
              min="1"
              max="100"
              value={topK}
              onChange={(e) => onTopKChange(parseInt(e.target.value) || 1)}
              disabled={loading}
              className={styles.select}
            />
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
              Bridge Table ({selectedEntries.size}/{bridgeTable.length}{" "}
              selected)
            </h2>
            <div className={styles.headerControls}>
              <input
                id="top-k-recreate"
                type="number"
                min="1"
                max="100"
                value={topK}
                onChange={(e) => onTopKChange(parseInt(e.target.value) || 1)}
                disabled={loading}
                className={styles.selectCompact}
                style={{ width: "80px" }}
              />
              <select
                id="join-method-recreate"
                value={joinMethod}
                onChange={(e) =>
                  onJoinMethodChange(e.target.value as JoinMethod)
                }
                disabled={loading}
                className={styles.selectCompact}
              >
                <option value="row">RS-JP</option>
                <option value="column">CS-JP-LP</option>
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

          <div className={styles.selectionControls}>
            <button onClick={onSelectAll} className={styles.selectButton}>
              Select All
            </button>
            <button onClick={onDeselectAll} className={styles.selectButton}>
              Deselect All
            </button>
          </div>

          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th className={styles.checkboxCell}>Select</th>
                  <th>R Value</th>
                  <th>S Value</th>
                  <th>NPMI Score</th>
                </tr>
              </thead>
              <tbody>
                {bridgeTable.map((entry, idx) => (
                  <tr
                    key={idx}
                    className={
                      selectedEntries.has(idx) ? styles.selectedRow : ""
                    }
                  >
                    <td className={styles.checkboxCell}>
                      <input
                        type="checkbox"
                        checked={selectedEntries.has(idx)}
                        onChange={() => onToggleEntry(idx)}
                      />
                    </td>
                    <td>{entry.r_val}</td>
                    <td>{entry.s_val}</td>
                    <td>{entry.npmi.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <button
            onClick={onPerformJoin}
            disabled={!canJoin || loading}
            className={styles.joinButton}
          >
            {loading ? "Joining..." : "Join Tables"}
          </button>
        </>
      )}
    </div>
  );
}
