// ParaPara 백엔드 API 클라이언트
// base: NEXT_PUBLIC_API_URL (예: http://localhost:8123) + /api/v1
// 인증: 로컬스토리지의 JWT 를 Authorization: Bearer 로 첨부.
//  - /products/analyze, /auth/google, /metadata/* 는 인증 불필요.

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "parapara_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}
export function setToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown; // 객체면 JSON, FormData 면 그대로
  auth?: boolean; // 기본 true
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, auth = true, headers, ...rest } = options;
  const h = new Headers(headers);

  if (auth) {
    const token = getToken();
    if (token) h.set("Authorization", `Bearer ${token}`);
  }
  h.set("ngrok-skip-browser-warning", "true");

  let payload: BodyInit | undefined;
  if (body instanceof FormData) {
    payload = body; // Content-Type 자동(boundary)
  } else if (body !== undefined) {
    h.set("Content-Type", "application/json");
    payload = JSON.stringify(body);
  }

  const res = await fetch(`${API_BASE}/api/v1${path}`, { ...rest, headers: h, body: payload });

  if (res.status === 204) return undefined as T;

  const text = await res.text();
  const data = text ? safeJson(text) : null;

  if (!res.ok) {
    const detail = (data as { detail?: unknown })?.detail;
    const message =
      typeof detail === "string" ? detail : `요청 실패 (HTTP ${res.status})`;
    throw new ApiError(res.status, message, detail);
  }
  return data as T;
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

// ─── 타입 (백엔드 스키마 기준) ───

export type ProductStatus = "draft" | "listing" | "listed" | "sold" | "unlisted";
export type ListingStatus = "pending" | "active" | "sold" | "removed";

export interface ProductImageOut {
  id: string;
  s3_key: string;
  order: number;
  url: string; // presigned S3 URL (백엔드 생성, 1시간 유효)
}

export interface ProductOut {
  id: string;
  user_id: string;
  title: string;
  brand: string;
  description: string;
  category: string;
  condition: number;
  price: number;
  status: ProductStatus;
  colors: string[];
  materials: string[];
  size: string | null;
  chest: number | null;
  total_length: number | null;
  waist: number | null;
  hip: number | null;
  rise: number | null;
  created_at: string;
  images: ProductImageOut[];
}

export interface ProductCreateBody {
  title: string;
  brand: string;
  description: string;
  category: string;
  condition: number; // 1~10 정수
  price: number; // > 0
  colors?: string[];
  materials?: string[];
  size?: string | null;
  chest?: number | null;
  total_length?: number | null;
  waist?: number | null;
  hip?: number | null;
  rise?: number | null;
  platforms: string[]; // 백엔드 활성: bunjang, junggonara
}

export interface ListingOut {
  id: string;
  product_id: string;
  platform: string;
  platform_product_id: string;
  status: ListingStatus;
  listed_at: string;
}

export interface AIAnalysisResult {
  title: string;
  brand: string;
  category: string;
  gender?: string;
  description: string;
  condition: number;
  size: string | null;
  chest: number | null;
  total_length: number | null;
  colors: string[];
  material: string[];
  pattern?: string;
  style?: string[];
  season?: string[];
}

// ─── 엔드포인트 ───

/** 사진 → AI 분석 (인증 불필요) */
export function analyzeImages(files: File[]): Promise<AIAnalysisResult> {
  const form = new FormData();
  files.forEach((f) => form.append("images", f));
  return request<AIAnalysisResult>("/products/analyze", {
    method: "POST",
    body: form,
    auth: false,
  });
}

export function createProduct(body: ProductCreateBody): Promise<ProductOut> {
  return request<ProductOut>("/products", { method: "POST", body });
}

export function uploadProductImages(
  productId: string,
  files: File[]
): Promise<ProductImageOut[]> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  return request<ProductImageOut[]>(`/products/${productId}/images`, {
    method: "POST",
    body: form,
  });
}

export function listProducts(status?: ProductStatus): Promise<ProductOut[]> {
  const q = status ? `?status=${status}` : "";
  return request<ProductOut[]>(`/products${q}`);
}

export function getProduct(id: string): Promise<ProductOut> {
  return request<ProductOut>(`/products/${id}`);
}

export function updateProduct(
  id: string,
  body: Partial<Pick<ProductCreateBody, "title" | "description" | "price" | "condition">>
): Promise<ProductOut> {
  return request<ProductOut>(`/products/${id}`, { method: "PATCH", body });
}

export function deleteProduct(id: string): Promise<void> {
  return request<void>(`/products/${id}`, { method: "DELETE" });
}

export function getListings(productId: string): Promise<ListingOut[]> {
  return request<ListingOut[]>(`/listings/${productId}`);
}

export function googleLogin(idToken: string): Promise<{ access_token: string; token_type: string }> {
  return request("/auth/google", {
    method: "POST",
    body: { id_token: idToken },
    auth: false,
  });
}

export interface MeOut {
  id: string;
  email: string;
  created_at: string;
}
export function getMe(): Promise<MeOut> {
  return request<MeOut>("/auth/me");
}

export function getMetadataOptions(): Promise<unknown> {
  return request("/metadata/options", { auth: false });
}

export interface PlatformAccountOut {
  id: string;
  platform: string;
  is_active: boolean;
  created_at: string;
}

export function listPlatformAccounts(): Promise<PlatformAccountOut[]> {
  return request<PlatformAccountOut[]>("/platform-accounts");
}

export function connectPlatform(platform: string, session_data: object): Promise<PlatformAccountOut> {
  return request<PlatformAccountOut>("/platform-accounts/session", {
    method: "POST",
    body: { platform, session_data },
  });
}

export function disconnectPlatform(accountId: string): Promise<void> {
  return request<void>(`/platform-accounts/${accountId}`, { method: "DELETE" });
}

export interface FitRequest {
  category?: string;
  size?: string;
  gender?: string;
  chest?: number | null;
  shoulder?: number | null;
  sleeve?: number | null;
  total_length?: number | null;
}
/** 표기 사이즈 + 실측 → 정핏/오버핏 추천 텍스트 (인증 불필요) */
export function fitRecommendation(body: FitRequest): Promise<{ text: string }> {
  return request("/products/fit-recommendation", {
    method: "POST",
    body,
    auth: false,
  });
}
