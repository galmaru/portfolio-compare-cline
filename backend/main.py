from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import init_db, get_db
from models.schemas import (
    StockSearchResult, StockItem,
    PortfolioCreate, PortfolioResponse,
    ComparisonRequest, ComparisonResult,
    PortfolioComparisonResult, DailyValue
)
from services.stock_data import search_stocks, get_stock_price_data

app = FastAPI(title="Portfolio Compare API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


# ==================== 주식 검색 API ====================

@app.get("/api/stocks/search", response_model=StockSearchResult)
def search_stock_api(keyword: str):
    """주식/ETF 검색"""
    if not keyword or len(keyword) < 1:
        return StockSearchResult(stocks=[])
    
    stocks = search_stocks(keyword)
    return StockSearchResult(stocks=[StockItem(**s) for s in stocks])


# ==================== 포트폴리오 API ====================

@app.post("/api/portfolios", response_model=PortfolioResponse)
def create_portfolio(portfolio: PortfolioCreate, db: Session = Depends(get_db)):
    """포트폴리오 생성"""
    from models.database import Portfolio, PortfolioItem
    
    # 비율 합계 검증
    total_ratio = sum(item.ratio for item in portfolio.items)
    if abs(total_ratio - 100.0) > 0.01:
        raise HTTPException(status_code=400, detail="비율의 합은 100%여야 합니다.")
    
    # 날짜 검증
    try:
        start = datetime.strptime(portfolio.start_date, "%Y-%m-%d")
        end = datetime.strptime(portfolio.end_date, "%Y-%m-%d")
        if start >= end:
            raise HTTPException(status_code=400, detail="시작일은 종료일보다 이전이어야 합니다.")
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다.")
    
    # 포트폴리오 저장
    db_portfolio = Portfolio(
        name=portfolio.name,
        total_amount=portfolio.total_amount,
        start_date=portfolio.start_date,
        end_date=portfolio.end_date
    )
    db.add(db_portfolio)
    db.flush()
    
    for item in portfolio.items:
        db_item = PortfolioItem(
            portfolio_id=db_portfolio.id,
            stock_code=item.stock_code,
            stock_name=item.stock_name,
            stock_type=item.stock_type,
            ratio=item.ratio
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_portfolio)
    
    return PortfolioResponse(
        id=db_portfolio.id,
        name=db_portfolio.name,
        total_amount=db_portfolio.total_amount,
        start_date=db_portfolio.start_date,
        end_date=db_portfolio.end_date,
        created_at=db_portfolio.created_at,
        items=[PortfolioResponse.items[0].__class__.model_validate(i) for i in db_portfolio.items]
    )


@app.get("/api/portfolios", response_model=List[PortfolioResponse])
def get_portfolios(db: Session = Depends(get_db)):
    """포트폴리오 목록 조회"""
    from models.database import Portfolio
    portfolios = db.query(Portfolio).order_by(Portfolio.created_at.desc()).all()
    return portfolios


@app.get("/api/portfolios/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """포트폴리오 상세 조회"""
    from models.database import Portfolio
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")
    return portfolio


@app.delete("/api/portfolios/{portfolio_id}")
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    """포트폴리오 삭제"""
    from models.database import Portfolio
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")
    
    db.delete(portfolio)
    db.commit()
    return {"message": "포트폴리오가 삭제되었습니다."}


# ==================== 비교 분석 API ====================

@app.post("/api/compare", response_model=ComparisonResult)
def compare_portfolios(request: ComparisonRequest, db: Session = Depends(get_db)):
    """포트폴리오 비교 분석"""
    from models.database import Portfolio
    
    results = []
    
    for portfolio_id in request.portfolio_ids:
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail=f"포트폴리오 {portfolio_id}를 찾을 수 없습니다.")
        
        # 포트폴리오 분석
        daily_values = analyze_portfolio(portfolio, db)
        results.append(daily_values)
    
    return ComparisonResult(results=results)


def analyze_portfolio(portfolio, db) -> PortfolioComparisonResult:
    """단일 포트폴리오 분석"""
    from models.database import PortfolioItem
    
    items = db.query(PortfolioItem).filter(PortfolioItem.portfolio_id == portfolio.id).all()
    
    # 각 종목별 일별 가격 데이터 조회
    all_prices = {}
    for item in items:
        prices = get_stock_price_data(item.stock_code, portfolio.start_date, portfolio.end_date)
        if prices is not None and not prices.empty:
            all_prices[item.stock_code] = prices
    
    # 일별 포트폴리오 가치 계산
    daily_values = []
    
    # 모든 거래일의 유니크한 날짜 수집
    all_dates = set()
    for code, prices in all_prices.items():
        if "Date" in prices.columns:
            all_dates.update(prices["Date"].tolist())
        elif "date" in prices.columns:
            all_dates.update(prices["date"].tolist())
    
    sorted_dates = sorted(list(all_dates))
    
    for date in sorted_dates:
        day_value = 0.0
        
        for item in items:
            if item.stock_code not in all_prices:
                continue
            
            prices = all_prices[item.stock_code]
            date_col = "Date" if "Date" in prices.columns else "date"
            
            # 해당 날짜의 가격 찾기
            date_prices = prices[prices[date_col] == date]
            
            if not date_prices.empty:
                close_price = float(date_prices.iloc[0]["Close"])
                
                # 보유 수량 계산: (총금액 * 비율 / 100) / 시작일 가격
                investment = portfolio.total_amount * (item.ratio / 100)
                
                # 시작일 가격 찾기
                start_prices = prices[prices[date_col] == portfolio.start_date]
                if start_prices.empty:
                    # 시작일 데이터가 없으면 가장 가까운 이전 데이터
                    before = prices[prices[date_col] <= portfolio.start_date]
                    if not before.empty:
                        start_price = float(before.iloc[-1]["Close"])
                    else:
                        continue
                else:
                    start_price = float(start_prices.iloc[0]["Close"])
                
                shares = investment / start_price
                day_value += shares * close_price
        
        if day_value > 0:
            # 시작일 가치 계산
            start_value = sum(
                (portfolio.total_amount * (item.ratio / 100))
                for item in items if item.stock_code in all_prices
            )
            
            return_rate = ((day_value - start_value) / start_value) * 100 if start_value > 0 else 0
            
            daily_values.append(DailyValue(
                date=date[:10] if len(date) > 10 else date,
                value=round(day_value, 2),
                return_rate=round(return_rate, 2)
            ))
    
    # 시작/종료 가치
    start_value = daily_values[0].value if daily_values else 0
    end_value = daily_values[-1].value if daily_values else 0
    return_rate = ((end_value - start_value) / start_value * 100) if start_value > 0 else 0
    
    return PortfolioComparisonResult(
        portfolio_id=portfolio.id,
        portfolio_name=portfolio.name,
        start_value=start_value,
        end_value=end_value,
        return_rate=round(return_rate, 2),
        daily_values=daily_values
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
