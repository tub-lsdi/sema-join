'use client';

import { useState } from 'react';
import Header from '@/components/Header';
import ErrorAlert from '@/components/ErrorAlert';
import TableUploadPanel from '@/components/TableUploadPanel';
import BridgeTablePanel from '@/components/BridgeTablePanel';
import JoinResultPanel from '@/components/JoinResultPanel';
import { createBridgeTable, joinFromBridge, type BridgeTableEntry } from '@/lib/api';
import styles from './page.module.css';

export default function Home() {
  // State
  const [tableR, setTableR] = useState<Array<Record<string, any>>>([]);
  const [tableS, setTableS] = useState<Array<Record<string, any>>>([]);
  const [rJoinCol, setRJoinCol] = useState('');
  const [sJoinCol, setSJoinCol] = useState('');
  const [bridgeTable, setBridgeTable] = useState<BridgeTableEntry[]>([]);
  const [joinResult, setJoinResult] = useState<Array<Record<string, any>>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Handlers
  const handleFileLoadR = (data: any[]) => {
    setTableR(data);
    setRJoinCol('');
    setBridgeTable([]);
    setJoinResult([]);
    setError('');
  };

  const handleFileLoadS = (data: any[]) => {
    setTableS(data);
    setSJoinCol('');
    setBridgeTable([]);
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
      const response = await createBridgeTable(listR, listS);
      setBridgeTable(response.bridge_table);
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

    setLoading(true);
    setError('');

    try {
      const response = await joinFromBridge(tableR, rJoinCol, bridgeTable, tableS, sJoinCol);
      setJoinResult(response.result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to perform join');
    } finally {
      setLoading(false);
    }
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
            onCreateBridge={handleCreateBridge}
            onPerformJoin={handleJoin}
            canCreate={!!(tableR.length && tableS.length && rJoinCol && sJoinCol)}
            canJoin={!!bridgeTable.length}
            loading={loading}
          />
        )}

        <JoinResultPanel data={joinResult} />
      </div>
    </div>
  );
}
