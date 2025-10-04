export interface Complex {
  id: number;
  complex_id: string;
  complex_name: string;
  complex_type?: string;
  total_households?: number;
  total_dongs?: number;
  completion_date?: string;
  min_area?: number;
  max_area?: number;
  min_price?: number;
  max_price?: number;
  min_lease_price?: number;
  max_lease_price?: number;
  latitude?: number;
  longitude?: number;
  created_at?: string;
  updated_at?: string;
}

export interface Article {
  id: number;
  article_no: string;
  complex_id: string;
  trade_type?: string;
  price?: string;
  price_change_state?: string;
  area_name?: string;
  area1?: number;
  area2?: number;
  floor_info?: string;
  direction?: string;
  building_name?: string;
  feature_desc?: string;
  tags?: string;
  realtor_name?: string;
  confirm_date?: string;
  is_active?: boolean;
  first_found_at?: string;
  last_seen_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Transaction {
  id: number;
  complex_id: string;
  trade_type?: string;
  trade_date?: string;
  deal_price?: number;
  formatted_price?: string;
  floor?: number;
  area?: number;
  exclusive_area?: number;
  created_at?: string;
}

export interface ComplexDetail extends Complex {
  articles?: Article[];
  transactions?: Transaction[];
}

export interface ComplexStats {
  complex_id: string;
  complex_name: string;
  articles: {
    total: number;
    sale: number;
    lease: number;
  };
  transactions: {
    total: number;
    recent?: Transaction;
  };
}

export interface PriceTrend {
  complex_id: string;
  complex_name: string;
  period_months: number;
  trend: {
    month: string;
    avg_price: number;
    min_price: number;
    max_price: number;
    count: number;
  }[];
}
