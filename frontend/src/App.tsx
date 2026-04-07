import React, { useState, useEffect } from 'react';
import { searchStocks, createPortfolio, getPortfolios, deletePortfolio, comparePortfolios } from './api';
import { StockItem, PortfolioResponse, PortfolioItemCreate } from './types';
import ComparisonChart from './components/ComparisonChart';
import './App.css';

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#6c9bcf', '#a288d4'];

function App() {
  const [portfolios, setPortfolios] = useState<PortfolioResponse[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [comparisonResult, setComparisonResult] = useState<any>(null);
  const [selectedPortfolios, setSelectedPortfolios] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadPortfolios();
  }, []);

  const loadPortfolios = async () => {
    try {
      const data = await getPortfolios();
      setPortfolios(data);
    } catch (error) {
      console.error('포트폴리오 로딩 실패:', error);
    }
  };

  const handleCreateSuccess = () => {
    setShowCreateForm(false);
    loadPortfolios();
  };

  const handleDelete = async (id: number) => {
    if (confirm('정말 삭제하시겠습니까?')) {
      try {
        await deletePortfolio(id);
        loadPortfolios();
      } catch (error) {
        alert('삭제에 실패했습니다.');
      }
    }
  };

  const handleCompare = async () => {
    if (selectedPortfolios.length < 2) {
      alert('비교할 포트폴리오를 2개 이상 선택해주세요.');
      return;
    }
    setLoading(true);
    try {
      const result = await comparePortfolios({ portfolio_ids: selectedPortfolios });
      setComparisonResult(result);
    } catch (error) {
      console.error('비교 분석 실패:', error);
      alert('비교 분석에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const togglePortfolio = (id: number) => {
    setSelectedPortfolios(prev =>
      prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
    );
  };

  return (
    <div className="app">
      <header className="header">
        <h1>📊 포트폴리오 비교</h1>
        <p>한국 주식/ETF 포트폴리오의 실적을 비교하세요</p>
      </header>

      <div className="container">
        <div className="controls">
          <button className="btn btn-primary" onClick={() => setShowCreateForm(!showCreateForm)}>
            {showCreateForm ? '취소' : '+ 새 포트폴리오'}
          </button>
          <button
            className="btn btn-success"
            onClick={handleCompare}
            disabled={selectedPortfolios.length < 2 || loading}
          >
            {loading ? '분석 중...' : `비교 시작 (${selectedPortfolios.length}개)`}
          </button>
        </div>

        {showCreateForm && (
          <PortfolioForm onSuccess={handleCreateSuccess} onCancel={() => setShowCreateForm(false)} />
        )}

        <div className="portfolio-list">
          <h2>포트폴리오 목록</h2>
          {portfolios.length === 0 ? (
            <p className="empty">아직 생성된 포트폴리오가 없습니다.</p>
          ) : (
            portfolios.map((portfolio) => (
              <div
                key={portfolio.id}
                className={`portfolio-card ${selectedPortfolios.includes(portfolio.id) ? 'selected' : ''}`}
                onClick={() => togglePortfolio(portfolio.id)}
              >
                <div className="card-header">
                  <input
                    type="checkbox"
                    checked={selectedPortfolios.includes(portfolio.id)}
                    onChange={() => togglePortfolio(portfolio.id)}
                    onClick={(e) => e.stopPropagation()}
                  />
                  <h3>{portfolio.name}</h3>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={(e) => { e.stopPropagation(); handleDelete(portfolio.id); }}
                  >
                    삭제
                  </button>
                </div>
                <div className="card-body">
                  <p>투자금액: {portfolio.total_amount.toLocaleString()}원</p>
                  <p>기간: {portfolio.start_date} ~ {portfolio.end_date}</p>
                  <div className="items">
                    {portfolio.items.map((item, idx) => (
                      <span key={idx} className="item-tag">
                        {item.stock_name} {item.ratio}%
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {comparisonResult && (
          <div className="comparison-result">
            <h2>비교 결과</h2>
            <div className="summary">
              {comparisonResult.results.map((r: any, idx: number) => (
                <div key={r.portfolio_id} className="summary-card" style={{ borderColor: COLORS[idx % COLORS.length] }}>
                  <h3 style={{ color: COLORS[idx % COLORS.length] }}>{r.portfolio_name}</h3>
                  <p>시작가: {r.start_value.toLocaleString()}원</p>
                  <p>종료가: {r.end_value.toLocaleString()}원</p>
                  <p className={r.return_rate >= 0 ? 'positive' : 'negative'}>
                    수익률: {r.return_rate.toFixed(2)}%
                  </p>
                </div>
              ))}
            </div>
            <ComparisonChart data={comparisonResult.results} colors={COLORS} />
          </div>
        )}
      </div>
    </div>
  );
}

// 포트폴리오 생성 폼
function PortfolioForm({ onSuccess, onCancel }: { onSuccess: () => void; onCancel: () => void }) {
  const [name, setName] = useState('');
  const [totalAmount, setTotalAmount] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [items, setItems] = useState<PortfolioItemCreate[]>([]);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [searchResults, setSearchResults] = useState<StockItem[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [step, setStep] = useState(1);

  // 어제 날짜 계산
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  const yesterdayStr = yesterday.toISOString().split('T')[0];

  useEffect(() => {
    if (searchKeyword.length >= 1) {
      setSearchLoading(true);
      const timer = setTimeout(async () => {
        try {
          const result = await searchStocks(searchKeyword);
          setSearchResults(result.stocks);
        } catch (error) {
          console.error('검색 실패:', error);
        } finally {
          setSearchLoading(false);
        }
      }, 300);
      return () => clearTimeout(timer);
    } else {
      setSearchResults([]);
    }
  }, [searchKeyword]);

  const addStock = (stock: StockItem) => {
    if (items.find(i => i.stock_code === stock.code)) {
      alert('이미 추가된 종목입니다.');
      return;
    }
    setItems([...items, {
      stock_code: stock.code,
      stock_name: stock.name,
      stock_type: stock.stock_type,
      ratio: 0
    }]);
    setSearchKeyword('');
    setSearchResults([]);
  };

  const updateRatio = (index: number, ratio: number) => {
    const newItems = [...items];
    newItems[index] = { ...newItems[index], ratio };
    setItems(newItems);
  };

  const removeItem = (index: number) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const totalRatio = items.reduce((sum, item) => sum + item.ratio, 0);

  const handleSubmit = async () => {
    if (!name) return alert('포트폴리오 이름을 입력해주세요.');
    if (!totalAmount || Number(totalAmount) <= 0) return alert('올바른 금액을 입력해주세요.');
    if (!startDate) return alert('시작일을 선택해주세요.');
    if (items.length === 0) return alert('종목을 추가해주세요.');
    if (Math.abs(totalRatio - 100) > 0.01) return alert('비율의 합이 100%가 되어야 합니다.');

    try {
      await createPortfolio({
        name,
        total_amount: Number(totalAmount),
        start_date: startDate,
        end_date: endDate || yesterdayStr,
        items
      });
      onSuccess();
    } catch (error: any) {
      alert(error.response?.data?.detail || '생성에 실패했습니다.');
    }
  };

  return (
    <div className="form-container">
      <h2>새 포트폴리오 생성</h2>

      <div className="form-group">
        <label>포트폴리오 이름</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="예: 기술주 포트폴리오"
        />
      </div>

      <div className="form-group">
        <label>투자 금액 (원)</label>
        <input
          type="number"
          value={totalAmount}
          onChange={(e) => setTotalAmount(e.target.value)}
          placeholder="10000000 (1천만원)"
          step="10000"
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>시작일</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            max={yesterdayStr}
          />
        </div>
        <div className="form-group">
          <label>종료일 (어제 고정)</label>
          <input type="text" value={yesterdayStr} disabled />
        </div>
      </div>

      <div className="form-group">
        <label>종목 검색 및 추가</label>
        <input
          type="text"
          value={searchKeyword}
          onChange={(e) => setSearchKeyword(e.target.value)}
          placeholder="종목명 또는 코드를 입력하세요 (예: 삼성전자, 005930)"
        />
        {searchLoading && <p className="loading">검색 중...</p>}
        {searchResults.length > 0 && (
          <div className="search-results">
            {searchResults.map(stock => (
              <div key={stock.code} className="search-item" onClick={() => addStock(stock)}>
                <span className="stock-code">{stock.code}</span>
                <span className="stock-name">{stock.name}</span>
                <span className="stock-type">{stock.stock_type === 'ETF' ? 'ETF' : '주식'}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {items.length > 0 && (
        <div className="items-list">
          <h3>추가된 종목 ({items.length}개)</h3>
          {items.map((item, idx) => (
            <div key={idx} className="item-row">
              <div className="item-info">
                <span className="item-name">{item.stock_name}</span>
                <span className="item-code">{item.stock_code}</span>
              </div>
              <div className="item-ratio">
                <input
                  type="number"
                  value={item.ratio}
                  onChange={(e) => updateRatio(idx, Number(e.target.value))}
                  placeholder="비율(%)"
                  min="0"
                  max="100"
                  step="0.1"
                />
                <span>%</span>
              </div>
              <button className="btn btn-danger btn-sm" onClick={() => removeItem(idx)}>X</button>
            </div>
          ))}
          <div className={`ratio-summary ${Math.abs(totalRatio - 100) < 0.01 ? 'valid' : 'invalid'}`}>
            비율 합계: {totalRatio.toFixed(1)}% {Math.abs(totalRatio - 100) < 0.01 ? '✓' : '(100%가 되어야 합니다)'}
          </div>
        </div>
      )}

      <div className="form-actions">
        <button className="btn btn-secondary" onClick={onCancel}>취소</button>
        <button className="btn btn-primary" onClick={handleSubmit}>포트폴리오 생성</button>
      </div>
    </div>
  );
}

export default App;