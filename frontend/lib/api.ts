const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types

export type JoinMethod = "row" | "column";

export type TableRow = Record<string, unknown>;

export interface BridgeTableEntry {
  r_val: string;
  s_val: string;
  npmi: number; // For RS-JP: single pairwise NPMI; For CS-JP-LP: aggregate column-level score
}

interface BridgeTableResponse {
  bridge_table: BridgeTableEntry[];
  total_r_values: number;
  total_s_values: number;
  total_candidates: number;
}

interface JoinResponse {
  result: TableRow[];
  total_records: number;
  total_r_records: number;
  matched_count: number;
}

export interface HistoryEntry {
  id: number;
  timestamp: string; // ISO datetime string
  r_join_col: string;
  s_join_col: string;
}

export interface HistoryResponse {
  entries: HistoryEntry[];
}

export interface HistoryDetailResponse extends HistoryEntry {
  list_r: any[];
  list_s: any[];
  bridge_table: any[];
  result: any[];
}

// Helper Functions

/**
 * Generic API request handler with error handling
 */
async function apiRequest<T>(url: string, options: RequestInit): Promise<T> {
  const response = await fetch(url, options);

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `Request failed with status ${response.status}`,
    }));
    throw new Error(error.detail || error.error || "Request failed");
  }

  return response.json();
}

// API Functions

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

export interface BridgeEntrySuggestion {
  r_val: string;
  selected_s_val: string;
  reason: string;
  confidence: number;
}

export interface BridgeEntrySuggestionResponse {
  selections: BridgeEntrySuggestion[];
  analysis: string;
  selected_indices: number[];
  model_used: string;
}

export interface OllamaStatus {
  ollama_running: boolean;
  model_requested?: string;
  model_available?: boolean;
  available_models?: string[];
  error?: string;
  suggestion?: string;
}

/**
 * Create a bridge table using the specified join algorithm
 */
export async function createBridgeTable(
  listR: string[],
  listS: string[],
  joinMethod: JoinMethod = "row",
  topK: number = 1
): Promise<BridgeTableResponse> {
  // Only send top_k for RS-JP (row method); CS-JP-LP ignores it
  const requestBody = {
    list_r: listR,
    list_s: listS,
    join_method: joinMethod,
    top_k: joinMethod === "row" ? topK : 1,
  };

  return apiRequest<BridgeTableResponse>(`${API_BASE_URL}/bridge-table`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(requestBody),
  });
}

/**
 * Perform join operation using the bridge table
 */
export async function joinFromBridge(
  listR: TableRow[],
  rJoinCol: string,
  bridgeTable: BridgeTableEntry[],
  listS: TableRow[],
  sJoinCol: string
): Promise<JoinResponse> {
  return apiRequest<JoinResponse>(`${API_BASE_URL}/join-from-bridge`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      list_r: listR,
      r_join_col: rJoinCol,
      bridge_table: bridgeTable,
      list_s: listS,
      s_join_col: sJoinCol,
    }),
  });
}

/**
 * Get AI recommendations for column matching between two tables
 */
export async function getAIColumnRecommendations(
  tableR: TableRow[],
  tableS: TableRow[],
  maxSamples: number = 100
): Promise<AIColumnMatchResponse> {
  return apiRequest<AIColumnMatchResponse>(`${API_BASE_URL}/ai/match-columns`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      table_r: tableR,
      table_s: tableS,
      max_samples: maxSamples,
    }),
  });
}

/**
 * Check if Ollama is running and which models are available
 */
export async function checkOllamaStatus(): Promise<OllamaStatus> {
  return apiRequest<OllamaStatus>(`${API_BASE_URL}/ai/status`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
}

/**
 * Get AI suggestions for best bridge table entries (for RS-JP with top_k > 1)
 */
export async function suggestBestBridgeEntries(
  bridgeEntries: BridgeTableEntry[]
): Promise<BridgeEntrySuggestionResponse> {
  return apiRequest<BridgeEntrySuggestionResponse>(
    `${API_BASE_URL}/ai/suggest-bridge-entries`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bridge_entries: bridgeEntries }),
    }
  );
}

export async function fetchHistory(): Promise<HistoryResponse> {
  return apiRequest<HistoryResponse>(`${API_BASE_URL}/history`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
}

export async function fetchHistoryDetail(
  id: number
): Promise<HistoryDetailResponse> {
  return apiRequest<HistoryDetailResponse>(`${API_BASE_URL}/history/${id}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
}
