/**
 * API client for semantic join backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types
export type JoinMethod = "row" | "column";

export interface BridgeTableEntry {
  r_val: string;
  s_val: string;
  pmi: number;
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

// History types
export interface HistoryEntry {
  id: number;
  timestamp: string; // ISO datetime string
  r_join_col: string;
  s_join_col: string;
}

export interface HistoryResponse {
  entries: HistoryEntry[];
}

// API Functions
export async function createBridgeTable(
  listR: string[],
  listS: string[],
  joinMethod: JoinMethod = "row",
  topK: number = 1
): Promise<BridgeTableResponse> {
  const response = await fetch(`${API_BASE_URL}/bridge-table`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      list_r: listR,
      list_s: listS,
      join_method: joinMethod,
      top_k: topK,
    }),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to create bridge table" }));
    throw new Error(error.detail);
  }

  return response.json();
}

export async function fetchHistory(): Promise<HistoryResponse> {
  const response = await fetch(`${API_BASE_URL}/history`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to fetch history" }));
    throw new Error(error.detail);
  }

  return response.json();
}

export async function fetchHistoryDetail(
  id: number
): Promise<
  HistoryEntry & {
    list_r: any[];
    list_s: any[];
    bridge_table: any[];
    result: any[];
  }
> {
  const response = await fetch(`${API_BASE_URL}/history/${id}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to fetch history detail" }));
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

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to perform join" }));
    throw new Error(error.detail);
  }

  return response.json();
}
