// 주식 검색
export interface StockItem {
  code: string;
  name: string;
  stock_type: string; // "STOCK" 또는 "ETF"
}

export interface StockSearchResult {
  stocks: StockItem[];
}

// 포트폴리오
export interface PortfolioItemCreate {
  stock_code: string;
  stock_name: string;
  stock_type: string;
  ratio: number;
}

export interface PortfolioCreate {
  name: string;
  total_amount: number;
  start_date: string;
  end_date: string;
  items: PortfolioItemCreate[];
}

export interface PortfolioItemResponse {
  id: number;
  stock_code: string;
  stock_name: string;
  stock_type: string;
  ratio: number;
}

export interface PortfolioResponse {
  id: number;
  name: string;
  total_amount: number;
  start_date: string;
  end_date: string;
  created_at: string;
  items: PortfolioItemResponse[];
}

// 비교 분석
export interface ComparisonRequest {
  portfolio_ids: number[];
}

export interface DailyValue {
  date: string;
  value: number;
  return_rate: number;
}

export interface PortfolioComparisonResult {
  portfolio_id: number;
  portfolio_name: string;
  start_value: number;
  end_value: number;
  return_rate: number;
  daily_values: DailyValue[];
}

export interface ComparisonResult {
  results: PortfolioComparisonResult[];
}