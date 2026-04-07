import axios from 'axios';
import {
  StockSearchResult,
  PortfolioCreate,
  PortfolioResponse,
  ComparisonRequest,
  ComparisonResult
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// 주식 검색
export const searchStocks = async (keyword: string): Promise<StockSearchResult> => {
  const response = await api.get(`/stocks/search?keyword=${encodeURIComponent(keyword)}`);
  return response.data;
};

// 포트폴리오 생성
export const createPortfolio = async (data: PortfolioCreate): Promise<PortfolioResponse> => {
  const response = await api.post('/portfolios', data);
  return response.data;
};

// 포트폴리오 목록 조회
export const getPortfolios = async (): Promise<PortfolioResponse[]> => {
  const response = await api.get('/portfolios');
  return response.data;
};

// 포트폴리오 상세 조회
export const getPortfolio = async (id: number): Promise<PortfolioResponse> => {
  const response = await api.get(`/portfolios/${id}`);
  return response.data;
};

// 포트폴리오 삭제
export const deletePortfolio = async (id: number): Promise<void> => {
  await api.delete(`/portfolios/${id}`);
};

// 포트폴리오 비교 분석
export const comparePortfolios = async (data: ComparisonRequest): Promise<ComparisonResult> => {
  const response = await api.post('/compare', data);
  return response.data;
};

export default api;