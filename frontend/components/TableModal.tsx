'use client';

import { useEffect } from 'react';
import styles from './TableModal.module.css';

interface TableModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  data: Array<Record<string, any>>;
  selectedColumn?: string;
}

export default function TableModal({
  isOpen,
  onClose,
  title,
  data,
  selectedColumn,
}: TableModalProps) {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const columns = data.length > 0 ? Object.keys(data[0]) : [];

  return (
    <div className={styles.overlay}>
      <div className={styles.backdrop} onClick={onClose} />

      <div className={styles.container}>
        <div className={styles.modal}>
          <div className={styles.header}>
            <div className={styles.headerContent}>
              <h3 className={styles.title}>{title}</h3>
              <p className={styles.subtitle}>
                {data.length} record{data.length !== 1 ? 's' : ''}
              </p>
            </div>
            <button
              onClick={onClose}
              className={styles.closeButton}
              aria-label="Close modal"
            >
              <svg
                className={styles.closeIcon}
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>

          <div className={styles.content}>
            <table className={styles.table}>
              <thead className={styles.tableHeader}>
                <tr>
                  <th className={styles.headerCellIndex}>
                    #
                  </th>
                  {columns.map((column) => {
                    const isSelected = selectedColumn === column;
                    return (
                      <th
                        key={column}
                        className={isSelected ? styles.headerCellSelected : styles.headerCell}
                      >
                        <div className={styles.checkmark}>
                          {isSelected && <span>✓</span>}
                          <span>{column}</span>
                        </div>
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody className={styles.tableBody}>
                {data.map((row, idx) => (
                  <tr key={idx} className={styles.row}>
                    <td className={styles.cellIndex}>
                      {idx + 1}
                    </td>
                    {columns.map((column) => {
                      const isSelectedCol = selectedColumn === column;
                      return (
                        <td
                          key={column}
                          className={isSelectedCol ? styles.cellHighlighted : styles.cell}
                        >
                          {typeof row[column] === 'object'
                            ? JSON.stringify(row[column])
                            : String(row[column] ?? '')}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className={styles.footer}>
            <button
              onClick={onClose}
              className={styles.footerButton}
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
