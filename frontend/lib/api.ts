import type { components, paths } from './api-types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Re-export types from auto-generated schema
export type JoinMethod = "row" | "column";
export type TableRow = Record<string, unknown>;

// Bridge Table Types
export type BridgeTableEntry = components['schemas']['BridgeTableEntry'];
type BridgeTableResponse = components['schemas']['BridgeTableResponse'];
type JoinResponse = components['schemas']['JoinResponse'];

// History Types
export type HistoryEntry = components['schemas']['HistoryEntry'];
export type HistoryResponse = components['schemas']['HistoryResponse'];
export type HistoryDetailResponse = components['schemas']['HistoryDetailEntry'];

// AI Types
export type AIColumnRecommendation = components['schemas']['AIColumnRecommendation'];
export type AIColumnRecommendationResponse = components['schemas']['AIColumnRecommendationResponse'];
export type AIBridgeRecommendation = components['schemas']['AIBridgeRecommendation'];
export type AIBridgeRecommendationResponse = components['schemas']['AIBridgeRecommendationResponse'];
export type AIOllamaStatus = components['schemas']['AIOllamaStatus'];

// Table Upload Types
export type UploadedTableMetadata = components['schemas']['UploadedTableMetadata'];
export type UploadedTableDetail = components['schemas']['UploadedTableDetail'];
export type UploadTableResponse = components['schemas']['UploadTableResponse'];
export type TablesListResponse = components['schemas']['TablesListResponse'];

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
): Promise<AIColumnRecommendationResponse> {
  return apiRequest<AIColumnRecommendationResponse>(`${API_BASE_URL}/ai/recommend-columns`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      table_r: tableR,
      table_s: tableS,
      max_samples: maxSamples,
    }),
  });
}

export async function checkOllamaStatus(): Promise<AIOllamaStatus> {
  return apiRequest<AIOllamaStatus>(`${API_BASE_URL}/ai/status`, {
    method: "GET",
  });
}

export async function getAIBridgeRecommendations(
  bridgeEntries: BridgeTableEntry[]
): Promise<AIBridgeRecommendationResponse> {
  return apiRequest<AIBridgeRecommendationResponse>(
    `${API_BASE_URL}/ai/recommend-bridge-entries`,
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
