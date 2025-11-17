"use client";

import { useState } from "react";
import {
  type BridgeTableEntry,
  type JoinMethod,
  getAIBridgeRecommendations,
} from "@/lib/api";
import { getErrorMessage, getScoreColumnConfig } from "@/lib/utils";
import styles from "./BridgeTablePanel.module.css";

interface Props {
  bridgeTable: BridgeTableEntry[];
  joinMethod: JoinMethod;
  bridgeTableMethod?: JoinMethod;
  topK: number;
  selectedEntries: Set<number>;
  onJoinMethodChange: (method: JoinMethod) => void;
  onTopKChange: (topK: number) => void;
  onCreateBridge: () => void;
  onPerformJoin: () => void;
  onToggleEntry: (index: number) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  onAISuggestBest: (indices: number[]) => void;
  canCreate: boolean;
  canJoin: boolean;
  loading: boolean;
}

export default function BridgeTablePanel({
  bridgeTable,
  joinMethod,
  bridgeTableMethod,
  topK,
  selectedEntries,
  onJoinMethodChange,
  onTopKChange,
  onCreateBridge,
  onPerformJoin,
  onToggleEntry,
  onSelectAll,
  onDeselectAll,
  onAISuggestBest,
  canCreate,
  canJoin,
  loading,
}: Props) {
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState("");

  const handleAIRecommend = async () => {
    setAiLoading(true);
    setAiError("");

    try {
      const result = await getAIBridgeRecommendations(bridgeTable);
      onAISuggestBest(result.recommended_indices);
    } catch (err) {
      setAiError(getErrorMessage(err, "Failed to get AI recommendations"));
    } finally {
      setAiLoading(false);
    }
  };

  // AI suggest button is only shown for RS-JP with top_k > 1
  const showAISuggestButton =
    joinMethod === "row" && topK > 1 && bridgeTable.length > 0;

  // Get score column configuration based on the algorithm that was used
  const scoreColumn = getScoreColumnConfig(bridgeTableMethod);

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
              <option value="row">RS-JP (Row Method)</option>
              <option value="column">CS-JP-LP (Column Method)</option>
            </select>

            {/* Algorithm Explanation */}
            <div className={styles.algoExplanation}>
              {joinMethod === "row" ? (
                <div className={styles.algoCard}>
                  <div className={styles.algoHeader}>
                    <strong>RS-JP: Row-Score Join Prediction</strong>
                    <span className={styles.algoBadge}>Baseline</span>
                  </div>
                  <div className={styles.algoDetails}>
                    <p className={styles.algoDescription}>
                      A greedy, per-row optimization algorithm that
                      independently identifies candidate matches for each value
                      based on pairwise NPMI scores derived from corpus
                      co-occurrence statistics.
                    </p>
                    <div className={styles.algoProperties}>
                      <div className={styles.propertyItem}>
                        <span className={styles.propertyLabel}>Approach:</span>
                        <span className={styles.propertyValue}>
                          Independent row-level matching
                        </span>
                      </div>
                      <div className={styles.propertyItem}>
                        <span className={styles.propertyLabel}>
                          Complexity:
                        </span>
                        <span className={styles.propertyValue}>
                          Simple and efficient
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className={styles.algoCard}>
                  <div className={styles.algoHeader}>
                    <strong>
                      CS-JP-LP: Column-Score Join Prediction with Linear
                      Programming
                    </strong>
                    <span className={styles.algoBadge}>Advanced</span>
                  </div>
                  <div className={styles.algoDetails}>
                    <p className={styles.algoDescription}>
                      A global optimization algorithm that formulates join
                      prediction as a Linear Program, maximizing aggregate
                      column-level PMI scores while ensuring consistent mapping
                      assignments across all rows.
                    </p>
                    <div className={styles.algoProperties}>
                      <div className={styles.propertyItem}>
                        <span className={styles.propertyLabel}>Approach:</span>
                        <span className={styles.propertyValue}>
                          Global consistency optimization
                        </span>
                      </div>
                      <div className={styles.propertyItem}>
                        <span className={styles.propertyLabel}>
                          Complexity:
                        </span>
                        <span className={styles.propertyValue}>
                          Polynomial time (LP relaxation + rounding)
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {joinMethod === "row" && (
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
              <p className={styles.helpText}>
                Number of candidate matches to show per row.
              </p>
            </div>
          )}

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
              selected) - {joinMethod === "row" ? "RS-JP" : "CS-JP-LP"}
            </h2>
            <div className={styles.headerControls}>
              {joinMethod === "row" && (
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
                  title="Top K matches per row"
                />
              )}
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
            <button
              type="button"
              onClick={onSelectAll}
              className={styles.selectButton}
            >
              Select All
            </button>
            <button
              type="button"
              onClick={onDeselectAll}
              className={styles.selectButton}
            >
              Deselect All
            </button>
            {showAISuggestButton && (
              <button
                type="button"
                onClick={handleAIRecommend}
                disabled={aiLoading || loading}
                className={styles.aiSuggestButton}
                title="Use AI to recommend the best match for each row"
              >
                {aiLoading ? (
                  <>
                    <span className={styles.spinner}></span>
                    AI Analyzing...
                  </>
                ) : (
                  <>
                    <span className={styles.icon}>✨</span>
                    AI Recommend Best
                  </>
                )}
              </button>
            )}
          </div>

          {aiError && (
            <div className={styles.aiError}>
              <strong>AI Error:</strong> {aiError}
            </div>
          )}

          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th className={styles.checkboxCell}>Select</th>
                  <th>
                    R Value
                    <span
                      className={styles.tooltipIcon}
                      title="Source values from the left input table (R)"
                    >
                      ⓘ
                    </span>
                  </th>
                  <th>
                    S Value
                    <span
                      className={styles.tooltipIcon}
                      title="Target values from the right input table (S)"
                    >
                      ⓘ
                    </span>
                  </th>
                  <th>
                    {scoreColumn.label}
                    <span
                      className={styles.tooltipIcon}
                      title={scoreColumn.tooltip}
                    >
                      ⓘ
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {bridgeTable.map((entry, idx) => (
                  <tr
                    key={idx}
                    className={
                      selectedEntries.has(idx) ? styles.selectedRow : ""
                    }
                    title={scoreColumn.tooltip}
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
