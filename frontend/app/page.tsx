'use client';

import { useState } from 'react';
import Header from '@/components/Header';
import ErrorAlert from '@/components/ErrorAlert';
import TableUploadPanel from '@/components/TableUploadPanel';
import BridgeTablePanel from '@/components/BridgeTablePanel';
import JoinResultPanel from '@/components/JoinResultPanel';
import { createBridgeTable, joinFromBridge, type BridgeTableEntry, type JoinMethod } from '@/lib/api';
import styles from './page.module.css';

export default function Home() {
  // State
  const [tableR, setTableR] = useState<Array<Record<string, any>>>([]);
  const [tableS, setTableS] = useState<Array<Record<string, any>>>([]);
  const [rJoinCol, setRJoinCol] = useState('');
  const [sJoinCol, setSJoinCol] = useState('');
  const [joinMethod, setJoinMethod] = useState<JoinMethod>('row');
  const [topK, setTopK] = useState<number>(5);
  const [bridgeTable, setBridgeTable] = useState<BridgeTableEntry[]>([]);
  const [selectedBridgeEntries, setSelectedBridgeEntries] = useState<Set<number>>(new Set());
  const [joinResult, setJoinResult] = useState<Array<Record<string, any>>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Handlers
  const handleFileLoadR = (data: any[]) => {
    setTableR(data);
    setRJoinCol('');
    setBridgeTable([]);
    setSelectedBridgeEntries(new Set());
    setJoinResult([]);
    setError('');
  };

  const handleFileLoadS = (data: any[]) => {
    setTableS(data);
    setSJoinCol('');
    setBridgeTable([]);
    setSelectedBridgeEntries(new Set());
    setJoinResult([]);
    setError('');
  };

  const handleCreateBridge = async () => {
    if (!tableR.length || !tableS.length || !rJoinCol || !sJoinCol) {
      setError('Please upload both files and select join columns');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const listR = tableR.map(row => String(row[rJoinCol]));
      const listS = tableS.map(row => String(row[sJoinCol]));
      const response = await createBridgeTable(listR, listS, joinMethod, topK);
      const bestMatchMap = new Map<string, { pmi: number, index: number }>();

      response.bridge_table.forEach((entry, index) => {
          const currentBest = bestMatchMap.get(entry.r_val);
          if (!currentBest || entry.pmi > currentBest.pmi) {
              bestMatchMap.set(entry.r_val, {pmi: entry.pmi, index: index});
          }
      });
      const initialSelection = new Set<number>(
          Array.from(bestMatchMap.values()).map(match => match.index)
      );

      setSelectedBridgeEntries(initialSelection);
      setJoinResult([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create bridge table');
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = async () => {
    if (!bridgeTable.length) {
      setError('Please create a bridge table first');
      return;
    }

    if (selectedBridgeEntries.size === 0) {
      setError('Please select at least one bridge table entry');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Filter bridge table to only include selected entries
      const selectedBridge = bridgeTable.filter((_, idx) => selectedBridgeEntries.has(idx));
      const response = await joinFromBridge(tableR, rJoinCol, selectedBridge, tableS, sJoinCol);
      setJoinResult(response.result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to perform join');
    } finally {
      setLoading(false);
    }
  };

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
            disabled={loading}
          />

          <TableUploadPanel
            title="Table S (Right Table)"
            data={tableS}
            selectedColumn={sJoinCol}
            onFileLoad={handleFileLoadS}
            onColumnSelect={setSJoinCol}
            disabled={loading}
          />
        </div>

        {(tableR.length > 0 || tableS.length > 0) && (
          <BridgeTablePanel
            bridgeTable={bridgeTable}
            joinMethod={joinMethod}
            topK={topK}
            selectedEntries={selectedBridgeEntries}
            onJoinMethodChange={setJoinMethod}
            onTopKChange={setTopK}
            onCreateBridge={handleCreateBridge}
            onPerformJoin={handleJoin}
            onToggleEntry={handleToggleBridgeEntry}
            onSelectAll={handleSelectAllBridge}
            onDeselectAll={handleDeselectAllBridge}
            canCreate={!!(tableR.length && tableS.length && rJoinCol && sJoinCol)}
            canJoin={!!bridgeTable.length && selectedBridgeEntries.size > 0}
            loading={loading}
          />
        )}

        <JoinResultPanel data={joinResult} />
      </div>
    </div>
  );
}
