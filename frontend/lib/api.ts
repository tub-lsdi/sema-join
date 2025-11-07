
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export type JoinMethod = 'row' | 'column';

export interface BridgeTableEntry {
  r_val: string;
  s_val: string;
  npmi: number;
}

interface BridgeTableResponse {
  bridge_table: BridgeTableEntry[];
  total_r_values: number;
  total_s_values: number;
  total_candidates: number;
}

interface JoinResponse {
  result: Array<Record<string, any>>;
  total_records: number;
  total_r_records: number;
  matched_count: number;
}

export interface ColumnJoinRecommendation {
  r_column: string;
  s_column: string;
  confidence: number;
  reason: string;
}

export interface AIColumnMatchResponse {
  recommended_joins: ColumnJoinRecommendation[];
  analysis: string;
  model_used: string;
  table_r_columns: string[];
  table_s_columns: string[];
  rows_analyzed_r: number;
  rows_analyzed_s: number;
}

export interface OllamaStatus {
  ollama_running: boolean;
  model_requested?: string;
  model_available?: boolean;
  available_models?: string[];
  error?: string;
  suggestion?: string;
}

// API Functions
export async function createBridgeTable(
  listR: string[],
  listS: string[],
  joinMethod: JoinMethod = 'row',
  topK: number = 1
): Promise<BridgeTableResponse> {
  const response = await fetch(`${API_BASE_URL}/bridge-table`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ list_r: listR, list_s: listS, join_method: joinMethod, top_k: topK }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to create bridge table' }));
    throw new Error(error.detail);
  }

  return response.json();
}

export async function joinFromBridge(
  listR: Array<Record<string, any>>,
  rJoinCol: string,
  bridgeTable: BridgeTableEntry[],
  listS: Array<Record<string, any>>,
  sJoinCol: string
): Promise<JoinResponse> {
  const response = await fetch(`${API_BASE_URL}/join-from-bridge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      list_r: listR,
      r_join_col: rJoinCol,
      bridge_table: bridgeTable,
      list_s: listS,
      s_join_col: sJoinCol,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to perform join' }));
    throw new Error(error.detail);
  }

  return response.json();
}

export async function getAIColumnRecommendations(
  tableR: Array<Record<string, any>>,
  tableS: Array<Record<string, any>>,
  maxSamples: number = 100
): Promise<AIColumnMatchResponse> {
  const response = await fetch(`${API_BASE_URL}/ai/match-columns`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      table_r: tableR,
      table_s: tableS,
      max_samples: maxSamples,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to get AI recommendations' }));
    throw new Error(error.detail || error.error || 'Failed to get AI recommendations');
  }

  return response.json();
}

export async function checkOllamaStatus(): Promise<OllamaStatus> {
  const response = await fetch(`${API_BASE_URL}/ai/status`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    throw new Error('Failed to check Ollama status');
  }

  return response.json();
}
