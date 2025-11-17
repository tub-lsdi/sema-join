'use client';

import { useState } from 'react';
import {
  getAIColumnRecommendations,
  type AIColumnRecommendationResponse,
  type AIColumnRecommendation,
  type TableRow,
} from '@/lib/api';
import {
  getErrorMessage,
  getConfidenceLabel,
  getConfidenceClassName,
  isOllamaNotRunningError,
  isModelNotFoundError,
} from '@/lib/utils';
import { DEFAULTS, ERROR_MESSAGES } from '@/lib/constants';
import styles from './AISuggestionPanel.module.css';

interface Props {
  tableR: TableRow[];
  tableS: TableRow[];
  onRecommendationAccept: (rColumn: string, sColumn: string) => void;
  disabled?: boolean;
}

export default function AISuggestionPanel({
  tableR,
  tableS,
  onRecommendationAccept,
  disabled = false,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<AIColumnRecommendationResponse | null>(null);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState(false);

  const handleGetRecommendations = async () => {
    if (!tableR.length || !tableS.length) {
      setError(ERROR_MESSAGES.MISSING_TABLES);
      return;
    }

    setLoading(true);
    setError('');
    setExpanded(true);

    try {
      const result = await getAIColumnRecommendations(
        tableR,
        tableS,
        DEFAULTS.MAX_AI_SAMPLES
      );
      setRecommendations(result);
    } catch (err) {
      const errorMessage = getErrorMessage(err, 'Failed to get AI recommendations');

      // Check for specific AI errors
      if (isOllamaNotRunningError(errorMessage)) {
        setError(ERROR_MESSAGES.AI_OLLAMA_NOT_RUNNING);
      } else if (isModelNotFoundError(errorMessage)) {
        setError(ERROR_MESSAGES.AI_MODEL_NOT_FOUND);
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptRecommendation = (recommendation: AIColumnRecommendation) => {
    onRecommendationAccept(recommendation.r_column, recommendation.s_column);
    setExpanded(false);
  };

  if (!tableR.length || !tableS.length) {
    return null;
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.titleSection}>
          <h3 className={styles.title}>
            <span className={styles.icon}>✨</span>
            AI Column Suggestions
          </h3>
          <p className={styles.subtitle}>
            Let AI analyze your tables and suggest which columns to join
          </p>
        </div>

        <button
          type="button"
          onClick={handleGetRecommendations}
          disabled={disabled || loading}
          className={styles.suggestButton}
        >
          {loading ? (
            <>
              <span className={styles.spinner}></span>
              Analyzing...
            </>
          ) : (
            <>
              <span className={styles.icon}>🤖</span>
              Get AI Recommendations
            </>
          )}
        </button>
      </div>

      {error && (
        <div className={styles.error}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {recommendations && expanded && (
        <div className={styles.results}>
          <div className={styles.analysis}>
            <h4>Analysis:</h4>
            <p>{recommendations.analysis}</p>
            <p className={styles.modelInfo}>
              <em>Powered by {recommendations.model_used}</em>
              {' • '}
              <em>Analyzed {recommendations.rows_analyzed_r} rows from Table R and {recommendations.rows_analyzed_s} rows from Table S</em>
            </p>
          </div>

          {recommendations.recommendations.length > 0 ? (
            <div className={styles.recommendations}>
              <h4>Recommended Joins:</h4>
              {recommendations.recommendations.map((rec, idx) => (
                <div key={idx} className={styles.recommendation}>
                  <div className={styles.recHeader}>
                    <div className={styles.columns}>
                      <span className={styles.columnBadge}>{rec.r_column}</span>
                      <span className={styles.arrow}>↔</span>
                      <span className={styles.columnBadge}>{rec.s_column}</span>
                    </div>
                    <div className={styles.confidence}>
                      <span
                        className={`${styles.confidenceBadge} ${getConfidenceClassName(
                          rec.confidence,
                          styles
                        )}`}
                      >
                        {getConfidenceLabel(rec.confidence)} (
                        {Math.round(rec.confidence * 100)}%)
                      </span>
                    </div>
                  </div>
                  <p className={styles.reason}>{rec.reason}</p>
                  <button
                    type="button"
                    onClick={() => handleAcceptRecommendation(rec)}
                    className={styles.acceptButton}
                    disabled={disabled}
                  >
                    ✓ Use This Join
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.noRecommendations}>
              <p>No strong recommendations found. Try selecting columns manually.</p>
            </div>
          )}

          <button
            type="button"
            onClick={() => setExpanded(false)}
            className={styles.closeButton}
          >
            Close
          </button>
        </div>
      )}
    </div>
  );
}
