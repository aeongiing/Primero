export type Platform = "bunjang" | "joonggonara" | "fruits" | "ebay" | "charan" | "karrot";

export type ProductStatus = "draft" | "listing" | "listed" | "sold" | "unlisted";

export type ListingStatus = "pending" | "active" | "sold" | "removed";

// ERD: users
export interface User {
  id: string;
  email: string;
  google_id: string;
  created_at: string;
}

// ERD: platform_accounts
export interface PlatformAccount {
  id: string;
  user_id: string;
  platform: Platform;
  credential_key: string;
  is_active: boolean;
}

// ERD: products
export interface Product {
  id: string;
  user_id: string;
  title: string;
  brand: string;
  description: string;
  category: string;
  condition: number; // 1~10
  price: number;
  status: ProductStatus;
  size: string | null;
  chest: number | null;
  total_length: number | null;
  waist: number | null;
  hip: number | null;
  rise: number | null;
  created_at: string;
  images?: ProductImage[];
  listings?: Listing[];
}

// ERD: product_images
export interface ProductImage {
  id: string;
  product_id: string;
  s3_key: string;
  order: number;
}

// ERD: listings
export interface Listing {
  id: string;
  product_id: string;
  platform_account_id: string;
  platform: Platform;
  platform_product_id: string;
  status: ListingStatus;
  listed_at: string;
}

// ERD: sales
export interface Sale {
  id: string;
  product_id: string;
  listing_id: string;
  platform: Platform;
  sold_at: string;
}

// 상품 등록 폼 (업로드 화면에서 사용)
export interface ProductUploadForm {
  images: File[];
  title: string;
  brand: string;
  description: string;
  category: string;
  condition: number;
  price: number;
  size: string;
  chest?: number;
  total_length?: number;
  waist?: number;
  hip?: number;
  rise?: number;
  platforms: Platform[];
}

// AI 분석 결과
export interface AIAnalysisResult {
  title: string;
  brand: string;
  category: string;
  description: string;
  condition: number;
  size: string;
  chest?: number;
  total_length?: number;
  waist?: number;
  hip?: number;
  rise?: number;
  colors: string[];
  material: string;
}
