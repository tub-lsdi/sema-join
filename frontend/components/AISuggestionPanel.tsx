'use client';

import { useState } from 'react';
import { getAIColumnRecommendations, type AIColumnMatchResponse, type ColumnJoinRecommendation } from '@/lib/api';
import styles from './AISuggestionPanel.module.css';

interface Props {
  tableR: Array<Record<string, any>>;
  tableS: Array<Record<string, any>>;
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
  const [recommendations, setRecommendations] = useState<AIColumnMatchResponse | null>(null);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState(false);

  const handleGetSuggestions = async () => {
    if (!tableR.length || !tableS.length) {
      setError('Please upload both tables first');
      return;
    }

    setLoading(true);
    setError('');
    setExpanded(true);

    try {
      // Send up to 100 rows from each table for better AI analysis
      const result = await getAIColumnRecommendations(tableR, tableS, 100);
      setRecommendations(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get AI recommendations';
      
      // Check for common errors
      if (errorMessage.includes('503') || errorMessage.includes('not available')) {
        setError('⚠️ Ollama is not running. Please start it with: ollama serve');
      } else if (errorMessage.includes('404') || errorMessage.includes('not available')) {
        setError('⚠️ AI model not found. Please install it with: ollama pull mistral');
      } else {
        setError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAcceptRecommendation = (recommendation: ColumnJoinRecommendation) => {
    onRecommendationAccept(recommendation.r_column, recommendation.s_column);
    setExpanded(false);
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.8) return styles.high;
    if (confidence >= 0.6) return styles.medium;
    return styles.low;
  };

  const getConfidenceLabel = (confidence: number): string => {
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.6) return 'Medium';
    return 'Low';
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
          onClick={handleGetSuggestions}
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
              Get AI Suggestions
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

          {recommendations.recommended_joins.length > 0 ? (
            <div className={styles.recommendations}>
              <h4>Recommended Joins:</h4>
              {recommendations.recommended_joins.map((rec, idx) => (
                <div key={idx} className={styles.recommendation}>
                  <div className={styles.recHeader}>
                    <div className={styles.columns}>
                      <span className={styles.columnBadge}>{rec.r_column}</span>
                      <span className={styles.arrow}>↔</span>
                      <span className={styles.columnBadge}>{rec.s_column}</span>
                    </div>
                    <div className={styles.confidence}>
                      <span className={`${styles.confidenceBadge} ${getConfidenceColor(rec.confidence)}`}>
                        {getConfidenceLabel(rec.confidence)} ({Math.round(rec.confidence * 100)}%)
                      </span>
                    </div>
                  </div>
                  <p className={styles.reason}>{rec.reason}</p>
                  <button
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

