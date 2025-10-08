export interface Complex {
  id: number;
  complex_id: string;
  complex_name: string;
  complex_type?: string;
  address?: string;  // 하위호환용 (도로명 주소 우선)
  road_address?: string;  // 도로명 주소
  jibun_address?: string;  // 지번(법정동) 주소
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
  monthly_rent?: string;
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
  same_addr_cnt?: number;
  same_addr_max_prc?: string;
  same_addr_min_prc?: string;
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
  complex_type?: string;
  address?: string;
  total_households?: number;
  articles: {
    total: number;
    sale: number;
    lease: number;
    monthly: number;
  };
  price_range?: {
    min: number;
    max: number;
  };
  changes_24h?: {
    new: number;
    removed: number;
    price_up: number;
    price_down: number;
    total: number;
  };
  min_price?: number;
  max_price?: number;
  transactions?: {
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

export interface ArticleChange {
  id: number;
  change_type: 'NEW' | 'REMOVED' | 'PRICE_UP' | 'PRICE_DOWN';
  article_no?: string;
  trade_type?: string;
  area_name?: string;
  building_name?: string;
  floor_info?: string;
  old_price?: string;
  new_price?: string;
  price_change_amount?: number;
  price_change_percent?: number;
  detected_at: string;
}

export interface ArticleChangeSummary {
  complex_id: string;
  hours: number;
  summary: {
    new: number;
    removed: number;
    price_up: number;
    price_down: number;
    total: number;
    most_significant_change?: ArticleChange;
  };
}

export interface ArticleChangeList {
  complex_id: string;
  hours: number;
  total: number;
  changes: ArticleChange[];
}

export interface TransactionAreaStats {
  exclusive_area: number;
  area_name: string;
  avg_price: number;
  min_price: number;
  max_price: number;
  count: number;
  formatted_avg_price: string;
}

export interface TransactionSummary {
  complex_id: string;
  complex_name: string;
  period_months: number;
  area_stats: TransactionAreaStats[];
}
