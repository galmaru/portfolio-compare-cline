from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# 주식 검색 관련
class StockItem(BaseModel):
    code: str
    name: str
    stock_type: str  # "STOCK" 또는 "ETF"


class StockSearchResult(BaseModel):
    stocks: List[StockItem]


# 포트폴리오 관련
class PortfolioItemCreate(BaseModel):
    stock_code: str
    stock_name: str
    stock_type: str
    ratio: float  # 비중 (%)


class PortfolioCreate(BaseModel):
    name: str
    total_amount: float  # 총 투자금액 (원)
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    items: List[PortfolioItemCreate]


class PortfolioItemResponse(BaseModel):
    id: int
    stock_code: str
    stock_name: str
    stock_type: str
    ratio: float

    class Config:
        from_attributes = True


class PortfolioResponse(BaseModel):
    id: int
    name: str
    total_amount: float
    start_date: str
    end_date: str
    created_at: datetime
    items: List[PortfolioItemResponse]

    class Config:
        from_attributes = True


# 비교 분석 관련
class ComparisonRequest(BaseModel):
    portfolio_ids: List[int]


class DailyValue(BaseModel):
    date: str
    value: float
    return_rate: float  # 시작가 대비 수익률 (%)


class PortfolioComparisonResult(BaseModel):
    portfolio_id: int
    portfolio_name: str
    start_value: float
    end_value: float
    return_rate: float
    daily_values: List[DailyValue]


class ComparisonResult(BaseModel):
    results: List[PortfolioComparisonResult]