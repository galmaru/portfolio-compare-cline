import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
import json
import requests

# 캐시 디렉토리
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# 한국 주식 종목 목록 (주요 종목)
KRX_STOCKS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "NAVER",
    "035720": "카카오",
    "005380": "현대차",
    "051910": "LG화학",
    "035250": "강원랜드",
    "006400": "삼성SDI",
    "068270": "셀트리온",
    "207940": "삼성바이오로직스",
    "003670": "포스코홀딩스",
    "028260": "삼성물산",
    "012330": "모바일리더",
    "066570": "LG전자",
    "096770": "SK이노베이션",
    "055550": "신한지주",
    "105560": "KB금융",
    "086790": "하나금융지주",
    "032830": "삼성생명",
    "000810": "삼성화재",
    "017670": "SK텔레콤",
    "030200": "KT",
    "032640": "LG유플러스",
    "003545": "LG",
    "010130": "고려아연",
    "003490": "대한항공",
    "039490": "기아",
    "009150": "삼성전기",
    "018260": "삼성SDS",
    "041510": "삼성에스디에스",
}

# ETF 목록
ETF_LIST = {
    "069500": "KODEX 200",
    "091160": "TIGER 200",
    "091170": "TIGER 은행",
    "069660": "KODEX 은행",
    "133690": "TIGER 차이나H",
    "091180": "TIGER 반도체",
    "091220": "TIGER 금융",
    "069500": "KODEX 200",
    "102580": "TIGER 차이나CSI300",
    "133690": "TIGER 차이나H",
    "195980": "TIGER 미국나스닥100",
    "360750": "TIGER 미국S&P500",
    "133690": "TIGER 차이나H",
    "091230": "TIGER 에너지화학",
    "069500": "KODEX 200",
    "114800": "TIGER 200건설",
    "133690": "TIGER 차이나H",
    "152100": "TIGER 200정보기술",
    "159819": "TIGER 200헬스케어",
    "305720": "TIGER 200품질",
    "148070": "TIGER 일본Nikkei225",
}


def search_stocks(keyword: str) -> List[Dict[str, str]]:
    """주식/ETF 검색"""
    results = []
    keyword_upper = keyword.upper()
    
    # KRX 종목 검색
    for code, name in KRX_STOCKS.items():
        if keyword_upper in name.upper() or keyword_upper in code:
            results.append({
                "code": code,
                "name": name,
                "stock_type": "STOCK"
            })
    
    # ETF 검색
    for code, name in ETF_LIST.items():
        if keyword_upper in name.upper() or keyword_upper in code:
            # 중복 체크
            if not any(r["code"] == code for r in results):
                results.append({
                    "code": code,
                    "name": name,
                    "stock_type": "ETF"
                })
    
    results.sort(key=lambda x: x["name"])
    return results[:100]


def get_stock_price_data(stock_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """특정 종목의 일별 가격 데이터 조회 (yfinance 사용)"""
    cache_key = f"{stock_code}_{start_date}_{end_date}".replace("-", "")
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    # 캐시 확인
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            return pd.DataFrame(cached_data)
        except:
            pass
    
    try:
        # yfinance로 데이터 조회 (한국 주식은 .KS 접미사 사용)
        ticker = f"{stock_code}.KS"
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if df is None or df.empty:
            return None
        
        # 컬럼 이름 정리
        df.columns = [col.lower() if isinstance(col, str) else col for col in df.columns]
        df = df.reset_index()
        
        # 날짜 컬럼 처리
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        
        # 캐시에 저장
        df.to_json(cache_file, orient="records", force_ascii=False)
        
        return df
    except Exception as e:
        print(f"주가 데이터 조회 오류 ({stock_code}): {e}")
        return None


def get_stock_price_at_date(stock_code: str, date: str) -> Optional[float]:
    """특정 날짜의 종목 가격 조회"""
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
        start_date = (target_date - timedelta(days=10)).strftime("%Y-%m-%d")
        end_date = (target_date + timedelta(days=10)).strftime("%Y-%m-%d")
        
        ticker = f"{stock_code}.KS"
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if df is None or df.empty:
            return None
        
        if isinstance(df.index, pd.DatetimeIndex):
            if target_date in df.index:
                return float(df.loc[target_date, "Close"])
            
            before = df.index[df.index <= target_date]
            if len(before) > 0:
                return float(df.loc[before[-1], "Close"])
        
        return None
    except Exception as e:
        print(f"특정 날짜 가격 조회 오류 ({stock_code}, {date}): {e}")
        return None


def clear_cache():
    """캐시 데이터 삭제"""
    import shutil
    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)
        os.makedirs(CACHE_DIR, exist_ok=True)
