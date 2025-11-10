import { type BridgeTableEntry, type JoinMethod } from './api';
import { CONFIDENCE_THRESHOLDS } from './constants';

export interface ScoreColumnConfig {
  label: string;
  tooltip: string;
}

/**
 * Type guard to check if error is an Error instance
 */
export function isError(error: unknown): error is Error {
  return error instanceof Error;
}

/**
 * Extract error message from unknown error type
 */
export function getErrorMessage(error: unknown, fallback: string): string {
  return isError(error) ? error.message : fallback;
}

/**
 * Get confidence level label based on numeric confidence score
 */
export function getConfidenceLabel(confidence: number): string {
  if (confidence >= CONFIDENCE_THRESHOLDS.HIGH) return 'High';
  if (confidence >= CONFIDENCE_THRESHOLDS.MEDIUM) return 'Medium';
  return 'Low';
}

/**
 * Get CSS class name for confidence level
 */
export function getConfidenceClassName(
  confidence: number,
  styles: Record<string, string>
): string {
  if (confidence >= CONFIDENCE_THRESHOLDS.HIGH) return styles.high || '';
  if (confidence >= CONFIDENCE_THRESHOLDS.MEDIUM) return styles.medium || '';
  return styles.low || '';
}

/**
 * Select best matches from bridge table entries
 * Returns indices of entries with highest NPMI per r_val
 */
export function selectBestMatches(bridgeTable: BridgeTableEntry[]): Set<number> {
  const bestMatchMap = new Map<string, { npmi: number; index: number }>();

  bridgeTable.forEach((entry, index) => {
    const currentBest = bestMatchMap.get(entry.r_val);
    if (!currentBest || entry.npmi > currentBest.npmi) {
      bestMatchMap.set(entry.r_val, { npmi: entry.npmi, index });
    }
  });

  return new Set(Array.from(bestMatchMap.values()).map((match) => match.index));
}

/**
 * Parse JSON file contents
 */
export function parseJSONFile(content: string): unknown[] {
  try {
    const parsed = JSON.parse(content);
    return Array.isArray(parsed) ? parsed : [parsed];
  } catch {
    throw new Error('Invalid JSON file');
  }
}

/**
 * Check if AI error is related to Ollama not running
 */
export function isOllamaNotRunningError(errorMessage: string): boolean {
  return errorMessage.includes('503') || errorMessage.includes('not available');
}

/**
 * Check if AI error is related to missing model
 */
export function isModelNotFoundError(errorMessage: string): boolean {
  return errorMessage.includes('404') || errorMessage.includes('not found');
}

/**
 * Get the score column header and tooltip text based on the join algorithm.
 * 
 * @param method - The join algorithm method (or undefined if no table has been created yet)
 * @returns An object containing the column label and tooltip text
 */
export function getScoreColumnConfig(
  method: JoinMethod | undefined
): ScoreColumnConfig {
  if (method === 'row') {
    return {
      label: 'NPMI Score',
      tooltip:
        'Normalized Pointwise Mutual Information: Quantifies pairwise statistical co-occurrence strength between values in the corpus. Range: [-1, +1]. Higher values indicate stronger semantic association.',
    };
  }
  
  if (method === 'column') {
    return {
      label: 'Match Score',
      tooltip:
        'Aggregate PMI score: Represents the sum of column-level co-occurrence scores for this assignment within the global optimization objective. Higher values indicate better consistency with the overall mapping.',
    };
  }
  
  return {
    label: 'Score',
    tooltip: 'Match score for this pairing',
  };
}
