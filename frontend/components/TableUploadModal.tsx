'use client';

import { useState, useRef } from 'react';
import { uploadTable } from '@/lib/api';
import styles from './TableUploadModal.module.css';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: () => void;
}

export default function TableUploadModal({
  isOpen,
  onClose,
  onUploadSuccess,
}: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    const ext = selectedFile.name.split('.').pop()?.toLowerCase();
    if (ext !== 'json' && ext !== 'csv') {
      setError('Please select a JSON or CSV file');
      return;
    }

    setFile(selectedFile);
    setError('');

    if (!name) {
      setName(selectedFile.name.replace(/\.(json|csv)$/i, ''));
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError('');

    try {
      await uploadTable(file, name || undefined, description || undefined);
      resetForm();
      onUploadSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const resetForm = () => {
    setFile(null);
    setName('');
    setDescription('');
    setError('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleClose = () => {
    if (uploading) return;
    resetForm();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className={styles.overlay} onClick={handleClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2>Upload Table to Database</h2>
          <button
            className={styles.closeButton}
            onClick={handleClose}
            disabled={uploading}
          >
            ×
          </button>
        </div>

        {error && (
          <div className={styles.error}>
            {error}
            <button onClick={() => setError('')}>×</button>
          </div>
        )}

        <div className={styles.content}>
          <div className={styles.formGroup}>
            <label htmlFor="file">File (JSON or CSV)*</label>
            <input
              ref={fileInputRef}
              id="file"
              type="file"
              accept=".json,.csv"
              onChange={handleFileChange}
              disabled={uploading}
              className={styles.fileInput}
            />
            {file && (
              <div className={styles.fileInfo}>
                Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
              </div>
            )}
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="name">Table Name</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Leave empty for auto-generated name"
              disabled={uploading}
              className={styles.textInput}
            />
            <div className={styles.hint}>
              If left empty, will use format: table_YYYYMMDD_HHMMSS
            </div>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="description">Description (optional)</label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add a description for this table..."
              disabled={uploading}
              className={styles.textArea}
              rows={3}
            />
          </div>
        </div>

        <div className={styles.footer}>
          <button
            className={styles.cancelButton}
            onClick={handleClose}
            disabled={uploading}
          >
            Cancel
          </button>
          <button
            className={styles.uploadButton}
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            {uploading ? 'Uploading...' : 'Upload'}
          </button>
        </div>
      </div>
    </div>
  );
}
