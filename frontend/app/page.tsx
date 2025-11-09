"use client";

import { useState } from "react";
import Header from "@/components/Header";
import ErrorAlert from "@/components/ErrorAlert";
import TableUploadPanel from "@/components/TableUploadPanel";
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
import { getErrorMessage, selectBestMatches } from "@/lib/utils";
import { DEFAULTS, ERROR_MESSAGES } from "@/lib/constants";
import styles from "./page.module.css";

export default function Home() {
  // State
  const [tableR, setTableR] = useState<TableRow[]>([]);
  const [tableS, setTableS] = useState<TableRow[]>([]);
  const [rJoinCol, setRJoinCol] = useState("");
  const [sJoinCol, setSJoinCol] = useState("");
  const [joinMethod, setJoinMethod] = useState<JoinMethod>("row");
  const [topK, setTopK] = useState<number>(DEFAULTS.TOP_K);
  const [bridgeTable, setBridgeTable] = useState<BridgeTableEntry[]>([]);
  const [bridgeTableMethod, setBridgeTableMethod] = useState<
    JoinMethod | undefined
  >(undefined);
  const [selectedBridgeEntries, setSelectedBridgeEntries] = useState<
    Set<number>
  >(new Set());
  const [joinResult, setJoinResult] = useState<TableRow[]>([]);
  const [joinResultMethod, setJoinResultMethod] = useState<
    JoinMethod | undefined
  >(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Handlers - File Operations

  const resetJoinState = () => {
    setBridgeTable([]);
    setBridgeTableMethod(undefined);
    setSelectedBridgeEntries(new Set());
    setJoinResult([]);
    setJoinResultMethod(undefined);
    setError("");
  };

  const handleFileLoadR = (data: TableRow[]) => {
    setTableR(data);
    setRJoinCol("");
    resetJoinState();
  };

  const handleFileLoadS = (data: TableRow[]) => {
    setTableS(data);
    setSJoinCol("");
    resetJoinState();
  };

  // Handlers - Bridge Table Operations

  const handleCreateBridge = async () => {
    if (!tableR.length || !tableS.length || !rJoinCol || !sJoinCol) {
      setError(ERROR_MESSAGES.MISSING_FILES);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const listR = tableR.map((row) => String(row[rJoinCol]));
      const listS = tableS.map((row) => String(row[sJoinCol]));

      const response = await createBridgeTable(listR, listS, joinMethod, topK);
      setBridgeTable(response.bridge_table);
      setBridgeTableMethod(joinMethod);

      // Auto-select best matches (highest NPMI per r_val)
      const initialSelection = selectBestMatches(response.bridge_table);
      setSelectedBridgeEntries(initialSelection);
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

    if (selectedBridgeEntries.size === 0) {
      setError(ERROR_MESSAGES.NO_SELECTION);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const selectedBridge = bridgeTable.filter((_, idx) =>
        selectedBridgeEntries.has(idx)
      );
      const response = await joinFromBridge(
        tableR,
        rJoinCol,
        selectedBridge,
        tableS,
        sJoinCol
      );
      setJoinResult(response.result);
      setJoinResultMethod(joinMethod);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to perform join"));
    } finally {
      setLoading(false);
    }
  };

  // Handlers - Selection Operations

  const handleToggleBridgeEntry = (index: number) => {
    const newSelected = new Set(selectedBridgeEntries);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedBridgeEntries(newSelected);
  };

  const handleSelectAllBridge = () => {
    setSelectedBridgeEntries(new Set(bridgeTable.map((_, idx) => idx)));
  };

  const handleDeselectAllBridge = () => {
    setSelectedBridgeEntries(new Set());
  };

  const handleAISuggestBest = (indices: number[]) => {
    setSelectedBridgeEntries(new Set(indices));
  };

  // Handlers - AI Recommendations

  const handleAIRecommendationAccept = (rColumn: string, sColumn: string) => {
    setRJoinCol(rColumn);
    setSJoinCol(sColumn);
    resetJoinState();
  };

  return (
    <div className={styles.container}>
      <div className={styles.wrapper}>
        <Header />
        <ErrorAlert message={error} />

        <div className={styles.gridTwoCols}>
          <TableUploadPanel
            title="Table R (Left Table)"
            data={tableR}
            selectedColumn={rJoinCol}
            onFileLoad={handleFileLoadR}
            onColumnSelect={setRJoinCol}
            onError={setError}
            disabled={loading}
          />

          <TableUploadPanel
            title="Table S (Right Table)"
            data={tableS}
            selectedColumn={sJoinCol}
            onFileLoad={handleFileLoadS}
            onColumnSelect={setSJoinCol}
            onError={setError}
            disabled={loading}
          />
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
            onJoinMethodChange={setJoinMethod}
            onTopKChange={setTopK}
            onCreateBridge={handleCreateBridge}
            onPerformJoin={handleJoin}
            onToggleEntry={handleToggleBridgeEntry}
            onSelectAll={handleSelectAllBridge}
            onDeselectAll={handleDeselectAllBridge}
            onAISuggestBest={handleAISuggestBest}
            canCreate={
              !!(tableR.length && tableS.length && rJoinCol && sJoinCol)
            }
            canJoin={!!bridgeTable.length && selectedBridgeEntries.size > 0}
            loading={loading}
          />
        )}

        <JoinResultPanel data={joinResult} joinMethod={joinResultMethod} />
      </div>
    </div>
  );
}
