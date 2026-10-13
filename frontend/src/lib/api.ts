import type {
  ApiError,
  Basis,
  ChatAnswer,
  ChatRequest,
  Compare,
  ChangeSet,
  ErrorCode,
  Freq,
  Health,
  MacroOutput,
  ModelCard,
  Overview,
  Prices,
  QuantOutput,
  Range,
  Returns,
  Transcription,
  Universe,
  Verdict,
} from "./types";

import healthMock from "../mocks/health.json";
import universeMock from "../mocks/universe.json";
import overviewMock from "../mocks/overview.json";
import pricesMock from "../mocks/prices.json";
import changesMock from "../mocks/changes.json";
import returnsMock from "../mocks/returns.json";
import compareMock from "../mocks/compare.json";
import quantMock from "../mocks/quant.json";
import modelCardMock from "../mocks/model_card.json";
import macroMock from "../mocks/macro.json";
import verdictMock from "../mocks/verdict.json";
import chatMock from "../mocks/chat.json";
import transcribeMock from "../mocks/transcribe.json";

export class ApiClientError extends Error implements ApiError {
  readonly status: number;
  readonly error: ApiError["error"];

  constructor(status: number, error: ApiError["error"]) {
    super(error.message);
    this.name = "ApiClientError";
    this.status = status;
    this.error = error;
  }
}

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === "true";
const API_BASE = (process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

// Scope is the server's call (404 NOT_IN_SCOPE); the client only normalises.
function normalizeSymbol(symbol: string): string {
  return symbol.trim().toUpperCase();
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  let res: Response;
  try {
    res = await fetch(url, {
      ...options,
      headers: {
        Accept: "application/json",
        ...options?.headers,
      },
    });
  } catch (err) {
    throw new ApiClientError(503, {
      code: "UPSTREAM",
      message: err instanceof Error ? err.message : "Network failure connecting to API server",
    });
  }

  if (!res.ok) {
    let errBody: ApiError | null = null;
    try {
      errBody = (await res.json()) as ApiError;
    } catch {
      // not JSON
    }

    if (errBody && errBody.error && errBody.error.code) {
      throw new ApiClientError(res.status, errBody.error);
    }

    const defaultCode: ErrorCode =
      res.status === 404
        ? "NOT_FOUND"
        : res.status === 400
        ? "BAD_REQUEST"
        : res.status === 429
        ? "RATE_LIMITED"
        : "UPSTREAM";

    throw new ApiClientError(res.status, {
      code: defaultCode,
      message: `Request failed with HTTP ${res.status}: ${res.statusText}`,
    });
  }

  return (await res.json()) as T;
}

// 1. GET /api/health
export async function getHealth(): Promise<Health> {
  if (USE_MOCKS) return healthMock as Health;
  return request<Health>("/api/health");
}

// 2. GET /api/universe
export async function getUniverse(): Promise<Universe> {
  if (USE_MOCKS) return universeMock as Universe;
  return request<Universe>("/api/universe");
}

// 3. GET /api/overview
export async function getOverview(basis: Basis = "calendar"): Promise<Overview> {
  if (USE_MOCKS) {
    const data = { ...(overviewMock as Overview) };
    data.basis = basis;
    return data;
  }
  return request<Overview>(`/api/overview?basis=${encodeURIComponent(basis)}`);
}

// 4. GET /api/prices/{symbol}
export async function getPrices(symbol: string, range: Range = "1Y"): Promise<Prices> {
  const clean = normalizeSymbol(symbol);
  if (USE_MOCKS) {
    return {
      ...(pricesMock as Prices),
      symbol: clean,
      range,
    };
  }
  return request<Prices>(`/api/prices/${encodeURIComponent(clean)}?range=${encodeURIComponent(range)}`);
}

// 5. GET /api/changes/{symbol}
export async function getChanges(symbol: string, basis: Basis = "calendar"): Promise<ChangeSet> {
  const clean = normalizeSymbol(symbol);
  if (USE_MOCKS) {
    return {
      ...(changesMock as ChangeSet),
      symbol: clean,
      basis,
    };
  }
  return request<ChangeSet>(
    `/api/changes/${encodeURIComponent(clean)}?basis=${encodeURIComponent(basis)}`
  );
}

// 6. GET /api/returns/{symbol}
export async function getReturns(
  symbol: string,
  freq: Freq = "M",
  basis: Basis = "calendar"
): Promise<Returns> {
  const clean = normalizeSymbol(symbol);
  if (USE_MOCKS) {
    return {
      ...(returnsMock as Returns),
      symbol: clean,
      freq,
      basis,
    };
  }
  return request<Returns>(
    `/api/returns/${encodeURIComponent(clean)}?freq=${encodeURIComponent(freq)}&basis=${encodeURIComponent(basis)}`
  );
}

// 7. GET /api/compare/{symbol}
export async function getCompare(symbol: string, range: Range = "1Y"): Promise<Compare> {
  const clean = normalizeSymbol(symbol);
  if (USE_MOCKS) {
    return {
      ...(compareMock as Compare),
      symbol: clean,
      range,
    };
  }
  return request<Compare>(
    `/api/compare/${encodeURIComponent(clean)}?range=${encodeURIComponent(range)}`
  );
}

// 8. GET /api/quant/{symbol}
export async function getQuant(symbol: string): Promise<QuantOutput> {
  const clean = normalizeSymbol(symbol);
  if (USE_MOCKS) {
    return {
      ...(quantMock as unknown as QuantOutput),
      symbol: clean,
    };
  }
  return request<QuantOutput>(`/api/quant/${encodeURIComponent(clean)}`);
}

// 9. GET /api/model/card
export async function getModelCard(): Promise<ModelCard> {
  if (USE_MOCKS) return modelCardMock as unknown as ModelCard;
  return request<ModelCard>("/api/model/card");
}

// 10. GET /api/macro
export async function getMacro(): Promise<MacroOutput> {
  if (USE_MOCKS) return macroMock as unknown as MacroOutput;
  return request<MacroOutput>("/api/macro");
}

// 11. GET /api/verdict/{symbol}
export async function getVerdict(symbol: string, refresh = false): Promise<Verdict> {
  // SCHEMA §4.2: STOCK only. Callers check SymbolInfo.type; the server answers NOT_IN_SCOPE otherwise.
  const clean = normalizeSymbol(symbol);
  if (USE_MOCKS) {
    return {
      ...(verdictMock as unknown as Verdict),
      symbol: clean,
    };
  }
  const query = refresh ? "?refresh=true" : "";
  return request<Verdict>(`/api/verdict/${encodeURIComponent(clean)}${query}`);
}

// 12. POST /api/chat
export async function postChat(req: ChatRequest): Promise<ChatAnswer> {
  if (USE_MOCKS) {
    return {
      ...(chatMock as unknown as ChatAnswer),
      question: req.question,
    };
  }
  return request<ChatAnswer>("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

// 13. POST /api/transcribe
export async function postTranscribe(audio: Blob | File): Promise<Transcription> {
  if (USE_MOCKS) return transcribeMock as Transcription;
  const formData = new FormData();
  formData.append("audio", audio);
  return request<Transcription>("/api/transcribe", {
    method: "POST",
    body: formData,
  });
}
