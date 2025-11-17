const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Common Types
export type JoinMethod = "row" | "column";
export type TableRow = Record<string, unknown>;

// Bridge Table Types
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
  result: TableRow[];
  total_records: number;
  total_r_records: number;
  matched_count: number;
}

// History Types
export interface HistoryEntry {
  id: number;
  timestamp: string;
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

// AI Types
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

// Table Upload Types
export interface UploadedTableMetadata {
  id: number;
  name: string;
  description: string | null;
  upload_timestamp: string;
  columns: string[];
  row_count: number;
}

export interface UploadedTableDetail extends UploadedTableMetadata {
  body: TableRow[];
}

export interface UploadTableResponse {
  id: number;
  name: string;
  message: string;
}

export interface TablesListResponse {
  tables: UploadedTableMetadata[];
  total: number;
}

// Helper
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

export async function createBridgeTable(
  listR: string[],
  listS: string[],
  joinMethod: JoinMethod = "row",
  topK: number = 1
): Promise<BridgeTableResponse> {
  return apiRequest<BridgeTableResponse>(`${API_BASE_URL}/bridge-table`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      list_r: listR,
      list_s: listS,
      join_method: joinMethod,
      top_k: joinMethod === "row" ? topK : 1,
    }),
  });
}

export async function joinFromBridge(
  tableRId: number,
  rJoinCol: string,
  bridgeTable: BridgeTableEntry[],
  tableSId: number,
  sJoinCol: string
): Promise<JoinResponse> {
  return apiRequest<JoinResponse>(`${API_BASE_URL}/join-from-bridge`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      table_r_id: tableRId,
      r_join_col: rJoinCol,
      bridge_table: bridgeTable,
      table_s_id: tableSId,
      s_join_col: sJoinCol,
    }),
  });
}

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

export async function checkOllamaStatus(): Promise<OllamaStatus> {
  return apiRequest<OllamaStatus>(`${API_BASE_URL}/ai/status`, {
    method: "GET",
  });
}

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
  });
}

export async function fetchHistoryDetail(id: number): Promise<HistoryDetailResponse> {
  return apiRequest<HistoryDetailResponse>(`${API_BASE_URL}/history/${id}`, {
    method: "GET",
  });
}

export async function uploadTable(
  file: File,
  name?: string,
  description?: string
): Promise<UploadTableResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (name) formData.append("name", name);
  if (description) formData.append("description", description);

  const response = await fetch(`${API_BASE_URL}/tables/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `Upload failed with status ${response.status}`,
    }));
    throw new Error(error.detail || error.error || "Upload failed");
  }

  return response.json();
}

export async function fetchTables(): Promise<TablesListResponse> {
  return apiRequest<TablesListResponse>(`${API_BASE_URL}/tables`, {
    method: "GET",
  });
}

export async function fetchTableById(tableId: number): Promise<UploadedTableDetail> {
  return apiRequest<UploadedTableDetail>(`${API_BASE_URL}/tables/${tableId}`, {
    method: "GET",
  });
}

export async function deleteTable(tableId: number): Promise<{ message: string }> {
  return apiRequest<{ message: string }>(`${API_BASE_URL}/tables/${tableId}`, {
    method: "DELETE",
  });
}
