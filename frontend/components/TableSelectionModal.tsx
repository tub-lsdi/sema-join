'use client';

import { useState, useEffect } from 'react';
import {
  fetchTables,
  fetchTableById,
  deleteTable,
  type UploadedTableMetadata,
  type TableRow
} from '@/lib/api';
import DataTable from './DataTable';
import styles from './TableSelectionModal.module.css';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (tableId: number, tableName: string, data: TableRow[]) => void;
  title?: string;
}

export default function TableSelectionModal({
  isOpen,
  onClose,
  onSelect,
  title = "Select Table",
}: Props) {
  const [tables, setTables] = useState<UploadedTableMetadata[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTableId, setSelectedTableId] = useState<number | null>(null);
  const [previewTableId, setPreviewTableId] = useState<number | null>(null);
  const [previewData, setPreviewData] = useState<TableRow[] | null>(null);
  const [previewTableName, setPreviewTableName] = useState<string>("");
  const [loadingPreview, setLoadingPreview] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadTables();
    }
  }, [isOpen]);

  const loadTables = async () => {
    setLoading(true);
    setError('');
    try {
      const { tables } = await fetchTables();
      setTables(tables);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tables');
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async (tableId: number, tableName: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setPreviewTableId(tableId);
    setPreviewTableName(tableName);
    setLoadingPreview(true);
    setPreviewData(null);

    try {
      const { body } = await fetchTableById(tableId);
      setPreviewData(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load preview');
    } finally {
      setLoadingPreview(false);
    }
  };

  const closePreview = () => {
    setPreviewTableId(null);
    setPreviewData(null);
    setPreviewTableName("");
  };

  const handleDelete = async (tableId: number, tableName: string) => {
    if (!confirm(`Delete table "${tableName}"?`)) return;

    try {
      await deleteTable(tableId);
      setTables(prev => prev.filter(t => t.id !== tableId));
      if (selectedTableId === tableId) setSelectedTableId(null);
      if (previewTableId === tableId) closePreview();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete');
    }
  };

  const handleSelect = async () => {
    if (!selectedTableId) return;

    try {
      const table = await fetchTableById(selectedTableId);
      onSelect(table.id, table.name, table.body);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load');
    }
  };

  const filteredTables = tables.filter(table =>
    table.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    table.columns.some(col => col.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  if (!isOpen) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2>{title}</h2>
          <button className={styles.closeButton} onClick={onClose}>
            ×
          </button>
        </div>

        {error && (
          <div className={styles.error}>
            {error}
            <button onClick={() => setError('')}>×</button>
          </div>
        )}

        <div className={styles.searchBar}>
          <input
            type="text"
            placeholder="Search tables by name or columns..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={styles.searchInput}
          />
        </div>

        <div className={styles.content}>
          {loading ? (
            <div className={styles.loading}>Loading tables...</div>
          ) : filteredTables.length === 0 ? (
            <div className={styles.empty}>
              {searchQuery ? 'No tables match your search' : 'No tables uploaded yet'}
            </div>
          ) : (
            <table className={styles.listTable}>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Rows</th>
                  <th>Columns</th>
                  <th>Uploaded</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredTables.map((table) => (
                  <tr
                    key={table.id}
                    className={selectedTableId === table.id ? styles.selected : ''}
                    onClick={() => setSelectedTableId(table.id)}
                  >
                    <td>
                      <strong>{table.name}</strong>
                      {table.description && (
                        <div className={styles.description}>{table.description}</div>
                      )}
                    </td>
                    <td>{table.row_count}</td>
                    <td>
                      <div className={styles.columnsList}>
                        {table.columns.slice(0, 3).join(', ')}
                        {table.columns.length > 3 && ` +${table.columns.length - 3} more`}
                      </div>
                    </td>
                    <td>{new Date(table.upload_timestamp).toLocaleString()}</td>
                    <td>
                      <div className={styles.actionButtons}>
                        <button
                          className={styles.previewButton}
                          onClick={(e) => handlePreview(table.id, table.name, e)}
                        >
                          Preview
                        </button>
                        <button
                          className={styles.deleteButton}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(table.id, table.name);
                          }}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className={styles.footer}>
          <button className={styles.cancelButton} onClick={onClose}>
            Cancel
          </button>
          <button
            className={styles.selectButton}
            onClick={handleSelect}
            disabled={!selectedTableId}
          >
            Select Table
          </button>
        </div>
      </div>

      {previewTableId && (
        <div className={styles.previewOverlay} onClick={closePreview}>
          <div className={styles.previewModal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.previewHeader}>
              <h2>Preview: {previewTableName}</h2>
              <button className={styles.closeButton} onClick={closePreview}>
                ×
              </button>
            </div>
            <div className={styles.previewContent}>
              {loadingPreview ? (
                <div className={styles.loading}>Loading preview...</div>
              ) : previewData ? (
                <DataTable data={previewData} showAll={true} />
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
