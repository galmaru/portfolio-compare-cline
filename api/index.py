from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import yfinance as yf
import sqlite3
import os

app = FastAPI(title="Portfolio Compare API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델
class StockItem(BaseModel):
    code: str
    name: str
    stock_type: str

class StockSearchResult(BaseModel):
    stocks: List[StockItem]

class PortfolioItemCreate(BaseModel):
    stock_code: str
    stock_name: str
    stock_type: str
    ratio: float

class PortfolioCreate(BaseModel):
    name: str
    total_amount: float
    start_date: str
    end_date: str
    items: List[PortfolioItemCreate]

class PortfolioItemResponse(BaseModel):
    id: int
    stock_code: str
    stock_name: str
    stock_type: str
    ratio: float

class PortfolioResponse(BaseModel):
    id: int
    name: str
    total_amount: float
    start_date: str
    end_date: str
    created_at: str
    items: List[PortfolioItemResponse]

class DailyValue(BaseModel):
    date: str
    value: float
    return_rate: float

class PortfolioComparisonResult(BaseModel):
    portfolio_id: int
    portfolio_name: str
    start_value: float
    end_value: float
    return_rate: float
    daily_values: List[DailyValue]

class ComparisonRequest(BaseModel):
    portfolio_ids: List[int]

class ComparisonResult(BaseModel):
    results: List[PortfolioComparisonResult]

# 한국 주식/ETF 목록
KOREAN_STOCKS = {
    "005930": {"name": "삼성전자", "type": "STOCK"},
    "000660": {"name": "SK하이닉스", "type": "STOCK"},
    "035420": {"name": "NAVER", "type": "STOCK"},
    "035720": {"name": "카카오", "type": "STOCK"},
    "005380": {"name": "현대차", "type": "STOCK"},
    "051910": {"name": "LG화학", "type": "STOCK"},
    "006400": {"name": "삼성SDI", "type": "STOCK"},
    "035580": {"name": "LG에너지솔루션", "type": "STOCK"},
    "028260": {"name": "삼성바이오로직스", "type": "STOCK"},
    "207940": {"name": "삼성바이오에피스", "type": "STOCK"},
    "003670": {"name": "포스코홀딩스", "type": "STOCK"},
    "068270": {"name": "셀트리온", "type": "STOCK"},
    "096770": {"name": "SK이노베이션", "type": "STOCK"},
    "012330": {"name": "현대모비스", "type": "STOCK"},
    "003490": {"name": "대한항공", "type": "STOCK"},
    "032830": {"name": "삼성생명", "type": "STOCK"},
    "086790": {"name": "하나금융지주", "type": "STOCK"},
    "105560": {"name": "KB금융", "type": "STOCK"},
    "055550": {"name": "신한지주", "type": "STOCK"},
    "015760": {"name": "한국전력", "type": "STOCK"},
}

KOREAN_ETFS = {
    "069500": {"name": "KODEX 200", "type": "ETF"},
    "102110": {"name": "TIGER 200", "type": "ETF"},
    "091160": {"name": "KODEX 반도체", "type": "ETF"},
    "091170": {"name": "TIGER 반도체", "type": "ETF"},
    "133690": {"name": "KODEX 미국나스닥100", "type": "ETF"},
    "133690KS": {"name": "TIGER 미국나스닥100", "type": "ETF"},
    "360750": {"name": "KODEX 미국S&P500", "type": "ETF"},
    "360750KS": {"name": "TIGER 미국S&P500", "type": "ETF"},
    "069660": {"name": "KODEX 은행", "type": "ETF"},
    "091180": {"name": "KODEX 증권", "type": "ETF"},
    "282330": {"name": "KODEX 차이나항셍테크", "type": "ETF"},
    "305720": {"name": "KODEX 일본Nikkei225", "type": "ETF"},
    "394400": {"name": "KODEX 미국필라델피아반도체", "type": "ETF"},
    "394400KS": {"name": "TIGER 미국필라델피아반도체", "type": "ETF"},
}

# DB 초기화
def get_db_path():
    return os.path.join(os.path.dirname(__file__), "portfolios.db")

def init_db():
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS portfolios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, total_amount REAL,
                  start_date TEXT, end_date TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS portfolio_items
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, portfolio_id INTEGER,
                  stock_code TEXT, stock_name TEXT, stock_type TEXT, ratio REAL,
                  FOREIGN KEY (portfolio_id) REFERENCES portfolios(id))''')
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# 주식 검색
def search_stocks(keyword: str) -> List[dict]:
    results = []
    keyword_lower = keyword.lower()
    keyword_upper = keyword.upper()
    
    # 주식 검색
    for code, info in KOREAN_STOCKS.items():
        if keyword_lower in info["name"].lower() or keyword_upper in code:
            results.append({"code": code, "name": info["name"], "stock_type": info["type"]})
    
    # ETF 검색
    for code, info in KOREAN_ETFS.items():
        if keyword_lower in info["name"].lower() or keyword_upper in code.upper():
            results.append({"code": code, "name": info["name"], "stock_type": info["type"]})
    
    return results

# 주식 데이터 가져오기
def get_stock_price_data(stock_code: str, start_date: str, end_date: str):
    try:
        # 한국 주식 코드 변환
        if stock_code.isdigit():
            ticker = f"{stock_code}.KS"
        else:
            ticker = stock_code
        
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            return None
        
        df = df.reset_index()
        df["Date"] = df["Date"].astype(str)
        return df[["Date", "Close"]]
    except Exception as e:
        print(f"Error fetching data for {stock_code}: {e}")
        return None

# API 엔드포인트
@app.get("/api/stocks/search", response_model=StockSearchResult)
def search_stock_api(keyword: str = ""):
    if not keyword or len(keyword) < 1:
        return StockSearchResult(stocks=[])
    stocks = search_stocks(keyword)
    return StockSearchResult(stocks=[StockItem(**s) for s in stocks])

@app.post("/api/portfolios", response_model=PortfolioResponse)
def create_portfolio(portfolio: PortfolioCreate):
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    total_ratio = sum(item.ratio for item in portfolio.items)
    if abs(total_ratio - 100.0) > 0.01:
        raise HTTPException(status_code=400, detail="비율의 합은 100%여야 합니다.")
    
    try:
        start = datetime.strptime(portfolio.start_date, "%Y-%m-%d")
        end = datetime.strptime(portfolio.end_date, "%Y-%m-%d")
        if start >= end:
            raise HTTPException(status_code=400, detail="시작일은 종료일보다 이전이어야 합니다.")
    except ValueError:
        raise HTTPException(status_code=400, detail="날짜 형식이 올바르지 않습니다.")
    
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO portfolios (name, total_amount, start_date, end_date, created_at) VALUES (?, ?, ?, ?, ?)",
              (portfolio.name, portfolio.total_amount, portfolio.start_date, portfolio.end_date, created_at))
    portfolio_id = c.lastrowid
    
    for item in portfolio.items:
        c.execute("INSERT INTO portfolio_items (portfolio_id, stock_code, stock_name, stock_type, ratio) VALUES (?, ?, ?, ?, ?)",
                  (portfolio_id, item.stock_code, item.stock_name, item.stock_type, item.ratio))
    
    conn.commit()
    
    # 응답 생성
    c.execute("SELECT * FROM portfolios WHERE id = ?", (portfolio_id,))
    p = dict(c.fetchone())
    
    c.execute("SELECT * FROM portfolio_items WHERE portfolio_id = ?", (portfolio_id,))
    items = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return PortfolioResponse(
        id=p["id"],
        name=p["name"],
        total_amount=p["total_amount"],
        start_date=p["start_date"],
        end_date=p["end_date"],
        created_at=p["created_at"],
        items=[PortfolioItemResponse(**i) for i in items]
    )

@app.get("/api/portfolios", response_model=List[PortfolioResponse])
def get_portfolios():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM portfolios ORDER BY created_at DESC")
    portfolios = [dict(row) for row in c.fetchall()]
    
    results = []
    for p in portfolios:
        c.execute("SELECT * FROM portfolio_items WHERE portfolio_id = ?", (p["id"],))
        items = [dict(row) for row in c.fetchall()]
        results.append(PortfolioResponse(
            id=p["id"],
            name=p["name"],
            total_amount=p["total_amount"],
            start_date=p["start_date"],
            end_date=p["end_date"],
            created_at=p["created_at"],
            items=[PortfolioItemResponse(**i) for i in items]
        ))
    
    conn.close()
    return results

@app.get("/api/portfolios/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: int):
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT * FROM portfolios WHERE id = ?", (portfolio_id,))
    p = c.fetchone()
    if not p:
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")
    
    p = dict(p)
    c.execute("SELECT * FROM portfolio_items WHERE portfolio_id = ?", (portfolio_id,))
    items = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return PortfolioResponse(
        id=p["id"],
        name=p["name"],
        total_amount=p["total_amount"],
        start_date=p["start_date"],
        end_date=p["end_date"],
        created_at=p["created_at"],
        items=[PortfolioItemResponse(**i) for i in items]
    )

@app.delete("/api/portfolios/{portfolio_id}")
def delete_portfolio(portfolio_id: int):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    
    c.execute("SELECT * FROM portfolios WHERE id = ?", (portfolio_id,))
    if not c.fetchone():
        raise HTTPException(status_code=404, detail="포트폴리오를 찾을 수 없습니다.")
    
    c.execute("DELETE FROM portfolio_items WHERE portfolio_id = ?", (portfolio_id,))
    c.execute("DELETE FROM portfolios WHERE id = ?", (portfolio_id,))
    conn.commit()
    conn.close()
    
    return {"message": "포트폴리오가 삭제되었습니다."}

@app.post("/api/compare", response_model=ComparisonResult)
def compare_portfolios(request: ComparisonRequest):
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    results = []
    for portfolio_id in request.portfolio_ids:
        c.execute("SELECT * FROM portfolios WHERE id = ?", (portfolio_id,))
        portfolio = c.fetchone()
        if not portfolio:
            raise HTTPException(status_code=404, detail=f"포트폴리오 {portfolio_id}를 찾을 수 없습니다.")
        
        portfolio = dict(portfolio)
        c.execute("SELECT * FROM portfolio_items WHERE portfolio_id = ?", (portfolio_id,))
        items = [dict(row) for row in c.fetchall()]
        
        # 일별 가치 계산
        daily_values = analyze_portfolio(portfolio, items)
        results.append(daily_values)
    
    conn.close()
    return ComparisonResult(results=results)

def analyze_portfolio(portfolio: dict, items: List[dict]) -> PortfolioComparisonResult:
    all_prices = {}
    for item in items:
        prices = get_stock_price_data(item["stock_code"], portfolio["start_date"], portfolio["end_date"])
        if prices is not None and not prices.empty:
            all_prices[item["stock_code"]] = prices
    
    daily_values = []
    all_dates = set()
    for code, prices in all_prices.items():
        if "Date" in prices.columns:
            all_dates.update(prices["Date"].tolist())
    
    sorted_dates = sorted(list(all_dates))
    
    for date in sorted_dates:
        day_value = 0.0
        for item in items:
            if item["stock_code"] not in all_prices:
                continue
            prices = all_prices[item["stock_code"]]
            date_prices = prices[prices["Date"] == date]
            if not date_prices.empty:
                close_price = float(date_prices.iloc[0]["Close"])
                investment = portfolio["total_amount"] * (item["ratio"] / 100)
                start_prices = prices[prices["Date"] <= portfolio["start_date"]]
                if start_prices.empty:
                    continue
                start_price = float(start_prices.iloc[-1]["Close"])
                shares = investment / start_price
                day_value += shares * close_price
        
        if day_value > 0:
            start_value = sum(
                (portfolio["total_amount"] * (item["ratio"] / 100))
                for item in items if item["stock_code"] in all_prices
            )
            return_rate = ((day_value - start_value) / start_value) * 100 if start_value > 0 else 0
            daily_values.append(DailyValue(
                date=date[:10] if len(date) > 10 else date,
                value=round(day_value, 2),
                return_rate=round(return_rate, 2)
            ))
    
    start_value = daily_values[0].value if daily_values else 0
    end_value = daily_values[-1].value if daily_values else 0
    return_rate = ((end_value - start_value) / start_value * 100) if start_value > 0 else 0
    
    return PortfolioComparisonResult(
        portfolio_id=portfolio["id"],
        portfolio_name=portfolio["name"],
        start_value=start_value,
        end_value=end_value,
        return_rate=round(return_rate, 2),
        daily_values=daily_values
    )

# DB 초기화
init_db()