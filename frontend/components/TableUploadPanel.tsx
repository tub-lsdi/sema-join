'use client';

import { useRef, useState } from 'react';
import InteractiveDataTable from './InteractiveDataTable';
import TableModal from './TableModal';
import styles from './TableUploadPanel.module.css';

interface Props {
  title: string;
  data: Array<Record<string, any>>;
  selectedColumn: string;
  onFileLoad: (data: any[]) => void;
  onColumnSelect: (column: string) => void;
  disabled?: boolean;
}

export default function TableUploadPanel({
  title,
  data,
  selectedColumn,
  onFileLoad,
  onColumnSelect,
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
        const json = JSON.parse(event.target?.result as string);
        const data = Array.isArray(json) ? json : [json];
        onFileLoad(data);
      } catch {
        alert('Invalid JSON file');
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
