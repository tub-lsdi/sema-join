'use client';

import { useRef, useState } from 'react';
import InteractiveDataTable from './InteractiveDataTable';
import TableModal from './TableModal';
import { type TableRow } from '@/lib/api';
import { parseJSONFile } from '@/lib/utils';
import { ERROR_MESSAGES } from '@/lib/constants';
import styles from './TableUploadPanel.module.css';

interface Props {
  title: string;
  data: TableRow[];
  selectedColumn: string;
  onFileLoad: (data: TableRow[]) => void;
  onColumnSelect: (column: string) => void;
  onError?: (error: string) => void;
  disabled?: boolean;
}

export default function TableUploadPanel({
  title,
  data,
  selectedColumn,
  onFileLoad,
  onColumnSelect,
  onError,
  disabled = false,
}: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showModal, setShowModal] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const content = event.target?.result as string;
        const parsedData = parseJSONFile(content);
        onFileLoad(parsedData as TableRow[]);
      } catch (error) {
        // Report error to parent if callback provided, otherwise use alert as fallback
        if (onError) {
          onError(ERROR_MESSAGES.INVALID_JSON);
        } else {
          alert(ERROR_MESSAGES.INVALID_JSON);
        }
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className={styles.panel}>
      {data.length === 0 ? (
        <div className={styles.empty}>
          <h2 className={styles.title}>{title}</h2>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleFileChange}
            disabled={disabled}
            className={styles.fileInput}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            className={styles.uploadButton}
          >
            Upload JSON File
          </button>
        </div>
      ) : (
        <>
          <div className={styles.header}>
            <h2 className={styles.titleSmall}>{title}</h2>
            <div className={styles.buttons}>
              {data.length > 5 && (
                <button
                  onClick={() => setShowModal(true)}
                  className={styles.viewAllButton}
                >
                  View All
                </button>
              )}
              <input
                type="file"
                accept=".json"
                onChange={handleFileChange}
                disabled={disabled}
                className={styles.fileInput}
                id={`upload-${title}`}
              />
              <label htmlFor={`upload-${title}`} className={styles.changeButton}>
                Change File
              </label>
            </div>
          </div>

          <InteractiveDataTable
            data={data}
            selectedColumn={selectedColumn}
            onColumnSelect={onColumnSelect}
          />

          {selectedColumn && (
            <div className={styles.indicator}>
              <strong>Selected:</strong> {selectedColumn}
            </div>
          )}

          <TableModal
            isOpen={showModal}
            onClose={() => setShowModal(false)}
            title={title}
            data={data}
            selectedColumn={selectedColumn}
          />
        </>
      )}
    </div>
  );
}
