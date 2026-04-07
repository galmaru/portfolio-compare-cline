from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./portfolios.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    total_amount = Column(Float, nullable=False)  # 총 투자금액 (원)
    start_date = Column(String(10), nullable=False)  # 시작일 (YYYY-MM-DD)
    end_date = Column(String(10), nullable=False)  # 종료일 (YYYY-MM-DD)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 포트폴리오에 포함된 종목들
    items = relationship("PortfolioItem", back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioItem(Base):
    __tablename__ = "portfolio_items"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    stock_code = Column(String(10), nullable=False)  # 종목 코드
    stock_name = Column(String(50), nullable=False)  # 종목명
    stock_type = Column(String(10), nullable=False)  # "STOCK" 또는 "ETF"
    ratio = Column(Float, nullable=False)  # 비중 (%)
    
    portfolio = relationship("Portfolio", back_populates="items")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()