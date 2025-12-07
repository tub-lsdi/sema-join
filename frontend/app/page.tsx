"use client";

import { useState } from "react";
import Header from "@/components/Header";
import ErrorAlert from "@/components/ErrorAlert";
import InteractiveDataTable from "@/components/InteractiveDataTable";
import DataTable from "@/components/DataTable";
import TableSelectionModal from "@/components/TableSelectionModal";
import TableUploadModal from "@/components/TableUploadModal";
import AISuggestionPanel from "@/components/AISuggestionPanel";
import BridgeTablePanel from "@/components/BridgeTablePanel";
import JoinResultPanel from "@/components/JoinResultPanel";
import {
  createBridgeTable,
  joinFromBridge,
  type BridgeTableEntry,
  type JoinMethod,
  type TableRow,
} from "@/lib/api";
import { getErrorMessage, selectBestMatches, getIndicesForRValue } from "@/lib/utils";
import { DEFAULTS, ERROR_MESSAGES } from "@/lib/constants";
import styles from "./page.module.css";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  const [tableR, setTableR] = useState<TableRow[]>([]);
  const [tableRId, setTableRId] = useState<number | null>(null);
  const [tableRName, setTableRName] = useState<string>("");
  const [tableS, setTableS] = useState<TableRow[]>([]);
  const [tableSId, setTableSId] = useState<number | null>(null);
  const [tableSName, setTableSName] = useState<string>("");

  const [rJoinCol, setRJoinCol] = useState("");
  const [sJoinCol, setSJoinCol] = useState("");
  const [joinMethod, setJoinMethod] = useState<JoinMethod>("row");
  const [topK, setTopK] = useState<number>(DEFAULTS.TOP_K);
  const [bridgeTable, setBridgeTable] = useState<BridgeTableEntry[]>([]);
  const [bridgeTableMethod, setBridgeTableMethod] = useState<JoinMethod | undefined>();
  const [selectedBridgeEntries, setSelectedBridgeEntries] = useState<Set<number>>(new Set());
  const [aiRecommendationEntries, setAiRecommendationEntries] = useState<Set<number>>(new Set());
  const [joinResult, setJoinResult] = useState<TableRow[]>([]);
  const [joinResultMethod, setJoinResultMethod] = useState<JoinMethod | undefined>();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showSelectionModal, setShowSelectionModal] = useState(false);
  const [selectingTableFor, setSelectingTableFor] = useState<"R" | "S" | null>(null);
  const [showFullTableModal, setShowFullTableModal] = useState(false);
  const [fullTableData, setFullTableData] = useState<{ name: string; data: TableRow[] } | null>(null);
  const resetJoinState = () => {
    setBridgeTable([]);
    setBridgeTableMethod(undefined);
    setSelectedBridgeEntries(new Set());
    setAiRecommendationEntries(new Set());
    setJoinResult([]);
    setJoinResultMethod(undefined);
    setError("");
  };

  const handleSelectTable = (id: number, name: string, data: TableRow[]) => {
    if (selectingTableFor === "R") {
      setTableR(data);
      setTableRId(id);
      setTableRName(name);
      setRJoinCol("");
    } else {
      setTableS(data);
      setTableSId(id);
      setTableSName(name);
      setSJoinCol("");
    }
    resetJoinState();
    setSelectingTableFor(null);
  };

  const handleOpenSelectTable = (tableType: "R" | "S") => {
    setSelectingTableFor(tableType);
    setShowSelectionModal(true);
  };

  const handleViewFullTable = (name: string, data: TableRow[]) => {
    setFullTableData({ name, data });
    setShowFullTableModal(true);
  };

  const handleCreateBridge = async () => {
    if (!tableR.length || !tableS.length || !rJoinCol || !sJoinCol) {
      setError(ERROR_MESSAGES.MISSING_FILES);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const listR = tableR.map(row => String(row[rJoinCol]));
      const listS = tableS.map(row => String(row[sJoinCol]));
      const { bridge_table } = await createBridgeTable(listR, listS, joinMethod, topK);

      setBridgeTable(bridge_table);
      setBridgeTableMethod(joinMethod);
      // For RS-JP (row method), select best matches per R value
      // For CS-JP-LP (column method), select all entries (optimal global assignment)
      if (joinMethod === "row") {
        setSelectedBridgeEntries(selectBestMatches(bridge_table));
      } else {
        setSelectedBridgeEntries(new Set(bridge_table.map((_, i) => i)));
      }
      setAiRecommendationEntries(new Set()); // Start with all unchecked
      setJoinResult([]);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to create bridge table"));
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = async () => {
    if (!bridgeTable.length) {
      setError(ERROR_MESSAGES.MISSING_BRIDGE);
      return;
    }
    if (!selectedBridgeEntries.size) {
      setError(ERROR_MESSAGES.NO_SELECTION);
      return;
    }
    if (!tableRId || !tableSId) {
      setError("Please reselect tables");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const selectedBridge = bridgeTable.filter((_, idx) => selectedBridgeEntries.has(idx));
      const { result } = await joinFromBridge(tableRId, rJoinCol, selectedBridge, tableSId, sJoinCol);

      setJoinResult(result);
      setJoinResultMethod(joinMethod);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to perform join"));
    } finally {
      setLoading(false);
    }
  };

  const handleToggleBridgeEntry = (index: number) => {
    const newSelected = new Set(selectedBridgeEntries);
    newSelected.has(index) ? newSelected.delete(index) : newSelected.add(index);
    setSelectedBridgeEntries(newSelected);
  };

  const handleToggleAIRecommendationEntry = (index: number) => {
    const newSelected = new Set(aiRecommendationEntries);
    newSelected.has(index) ? newSelected.delete(index) : newSelected.add(index);
    setAiRecommendationEntries(newSelected);
  };

  const handleToggleAIRecommendationByRValue = (rValue: string) => {
    const indices = getIndicesForRValue(bridgeTable, rValue);
    const newSelected = new Set(aiRecommendationEntries);

    // Check if all indices for this R value are already selected
    const allSelected = indices.every(idx => aiRecommendationEntries.has(idx));

    if (allSelected) {
      // Deselect all for this R value
      indices.forEach(idx => newSelected.delete(idx));
    } else {
      // Select all for this R value
      indices.forEach(idx => newSelected.add(idx));
    }

    setAiRecommendationEntries(newSelected);
  };

  const handleAIRecommendationAccept = (rColumn: string, sColumn: string) => {
    setRJoinCol(rColumn);
    setSJoinCol(sColumn);
    resetJoinState();
  };

  return (
    <div className={styles.container}>
      <div className={styles.wrapper}>
        <Header />
        {error && <ErrorAlert message={error} />}

        <div className={styles.topCard}>
          <div className={styles.actionButtons}>
            <button
              className={styles.uploadButton}
              onClick={() => setShowUploadModal(true)}
            >
              Upload to Database
            </button>
            <button
              className={styles.historyButton}
              onClick={() => router.push("/history")}
            >
              View History
            </button>
          </div>
        </div>

        <div className={styles.gridTwoCols}>
          <div className={styles.tablePanel}>
            {tableR.length === 0 ? (
              <div className={styles.emptyPanel}>
                <h2 className={styles.title}>Table R (Left Table)</h2>
                <p className={styles.emptyMessage}>No table selected</p>
                <button
                  className={styles.selectTableButton}
                  onClick={() => handleOpenSelectTable("R")}
                  disabled={loading}
                >
                  Select Table R
                </button>
              </div>
            ) : (
              <>
                <div className={styles.panelHeader}>
                  <h2 className={styles.titleSmall}>
                    Table R: {tableRName}
                  </h2>
                  <div className={styles.headerButtons}>
                    <button
                      className={styles.viewFullButton}
                      onClick={() => handleViewFullTable(tableRName, tableR)}
                      disabled={loading}
                    >
                      View Full Table
                    </button>
                    <button
                      className={styles.changeButton}
                      onClick={() => handleOpenSelectTable("R")}
                      disabled={loading}
                    >
                      Change Table
                    </button>
                  </div>
                </div>
                <div className={styles.tableContainer}>
                  <InteractiveDataTable
                    data={tableR}
                    selectedColumn={rJoinCol}
                    onColumnSelect={setRJoinCol}
                  />
                </div>
                {rJoinCol && (
                  <div className={styles.indicator}>
                    <strong>Selected:</strong> {rJoinCol}
                  </div>
                )}
              </>
            )}
          </div>

          <div className={styles.tablePanel}>
            {tableS.length === 0 ? (
              <div className={styles.emptyPanel}>
                <h2 className={styles.title}>Table S (Right Table)</h2>
                <p className={styles.emptyMessage}>No table selected</p>
                <button
                  className={styles.selectTableButton}
                  onClick={() => handleOpenSelectTable("S")}
                  disabled={loading}
                >
                  Select Table S
                </button>
              </div>
            ) : (
              <>
                <div className={styles.panelHeader}>
                  <h2 className={styles.titleSmall}>
                    Table S: {tableSName}
                  </h2>
                  <div className={styles.headerButtons}>
                    <button
                      className={styles.viewFullButton}
                      onClick={() => handleViewFullTable(tableSName, tableS)}
                      disabled={loading}
                    >
                      View Full Table
                    </button>
                    <button
                      className={styles.changeButton}
                      onClick={() => handleOpenSelectTable("S")}
                      disabled={loading}
                    >
                      Change Table
                    </button>
                  </div>
                </div>
                <div className={styles.tableContainer}>
                  <InteractiveDataTable
                    data={tableS}
                    selectedColumn={sJoinCol}
                    onColumnSelect={setSJoinCol}
                  />
                </div>
                {sJoinCol && (
                  <div className={styles.indicator}>
                    <strong>Selected:</strong> {sJoinCol}
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {tableR.length > 0 && tableS.length > 0 && (
          <AISuggestionPanel
            tableR={tableR}
            tableS={tableS}
            onRecommendationAccept={handleAIRecommendationAccept}
            disabled={loading}
          />
        )}

        {(tableR.length > 0 || tableS.length > 0) && (
          <BridgeTablePanel
            bridgeTable={bridgeTable}
            joinMethod={joinMethod}
            bridgeTableMethod={bridgeTableMethod}
            topK={topK}
            selectedEntries={selectedBridgeEntries}
            aiRecommendationEntries={aiRecommendationEntries}
            onJoinMethodChange={setJoinMethod}
            onTopKChange={setTopK}
            onCreateBridge={handleCreateBridge}
            onPerformJoin={handleJoin}
            onToggleEntry={handleToggleBridgeEntry}
            onToggleAIRecommendationEntry={handleToggleAIRecommendationEntry}
            onToggleAIRecommendationByRValue={handleToggleAIRecommendationByRValue}
            onSelectAll={() => setSelectedBridgeEntries(new Set(bridgeTable.map((_, i) => i)))}
            onDeselectAll={() => setSelectedBridgeEntries(new Set())}
            onSelectAllAIRecommendation={() => setAiRecommendationEntries(new Set(bridgeTable.map((_, i) => i)))}
            onDeselectAllAIRecommendation={() => setAiRecommendationEntries(new Set())}
            onAISuggestBest={(recommendedIndices, sentForRecommendation) => {
              // Keep selections that weren't sent for recommendation
              const newSelected = new Set(selectedBridgeEntries);

              // Remove all entries that were sent for recommendation
              sentForRecommendation.forEach(idx => newSelected.delete(idx));

              // Add only the recommended indices
              recommendedIndices.forEach(idx => newSelected.add(idx));

              setSelectedBridgeEntries(newSelected);

              // Clear AI recommendation selections after recommendations are made
              setAiRecommendationEntries(new Set());
            }}
            canCreate={
              !!(tableR.length && tableS.length && rJoinCol && sJoinCol)
            }
            canJoin={!!bridgeTable.length && selectedBridgeEntries.size > 0}
            loading={loading}
          />
        )}

        <JoinResultPanel
          data={joinResult}
          joinMethod={joinResultMethod}
          onViewFullTable={() => handleViewFullTable("Join Result", joinResult)}
        />
      </div>

      <TableUploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUploadSuccess={() => setError("")}
      />

      <TableSelectionModal
        isOpen={showSelectionModal}
        onClose={() => {
          setShowSelectionModal(false);
          setSelectingTableFor(null);
        }}
        onSelect={handleSelectTable}
        title={`Select Table ${selectingTableFor} (${selectingTableFor === "R" ? "Left" : "Right"} Table)`}
      />

      {showFullTableModal && fullTableData && (
        <div className={styles.fullTableOverlay} onClick={() => setShowFullTableModal(false)}>
          <div className={styles.fullTableModal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.fullTableHeader}>
              <h2>{fullTableData.name}</h2>
              <button className={styles.closeButton} onClick={() => setShowFullTableModal(false)}>
                ×
              </button>
            </div>
            <div className={styles.fullTableContent}>
              <DataTable data={fullTableData.data} showAll />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
