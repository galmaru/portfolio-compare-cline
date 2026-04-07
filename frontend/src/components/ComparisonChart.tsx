import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface DailyValue {
  date: string;
  value: number;
  return_rate: number;
}

interface PortfolioResult {
  portfolio_id: number;
  portfolio_name: string;
  start_value: number;
  end_value: number;
  return_rate: number;
  daily_values: DailyValue[];
}

interface ComparisonChartProps {
  data: PortfolioResult[];
  colors: string[];
}

const ComparisonChart: React.FC<ComparisonChartProps> = ({ data, colors }) => {
  const [chartType, setChartType] = React.useState<'value' | 'return'>('return');

  // 차트 데이터 가공
  const chartData = React.useMemo(() => {
    if (data.length === 0) return [];

    // 모든 포트폴리오의 날짜를 수집
    const dateMap = new Map<string, Record<string, any>>();

    data.forEach((portfolio, idx) => {
      const key = `portfolio_${idx}`;
      portfolio.daily_values.forEach((dv) => {
        if (!dateMap.has(dv.date)) {
          dateMap.set(dv.date, { date: dv.date });
        }
        const entry = dateMap.get(dv.date)!;
        if (chartType === 'value') {
          entry[key] = dv.value;
        } else {
          entry[key] = dv.return_rate;
        }
      });
    });

    // 날짜순 정렬
    return Array.from(dateMap.values())
      .sort((a, b) => (a.date > b.date ? 1 : -1))
      .map((entry) => {
        const result: Record<string, any> = { ...entry };
        // 누락된 날짜의 데이터는 이전 값으로 채우기
        return result;
      });
  }, [data, chartType]);

  // 날짜 포맷팅
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  // Y축 포맷팅
  const formatYAxis = (value: number) => {
    if (chartType === 'value') {
      if (value >= 100000000) {
        return `${(value / 100000000).toFixed(0)}억`;
      } else if (value >= 10000) {
        return `${(value / 10000).toFixed(0)}만`;
      }
      return value.toLocaleString();
    }
    return `${value.toFixed(1)}%`;
  };

  const formatTooltip = (value: number) => {
    if (chartType === 'value') {
      return `${value.toLocaleString()}원`;
    }
    return `${value.toFixed(2)}%`;
  };

  return (
    <div className="chart-container">
      <div className="chart-controls">
        <button
          className={`chart-toggle ${chartType === 'return' ? 'active' : ''}`}
          onClick={() => setChartType('return')}
        >
          수익률 비교
        </button>
        <button
          className={`chart-toggle ${chartType === 'value' ? 'active' : ''}`}
          onClick={() => setChartType('value')}
        >
          금액 비교
        </button>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            interval="preserveStartEnd"
          />
          <YAxis tickFormatter={formatYAxis} />
          <Tooltip
            labelFormatter={formatDate}
            formatter={formatTooltip}
          />
          <Legend
            formatter={(value: string, entry: any) => {
              const idx = parseInt(value.split('_')[1]);
              return data[idx]?.portfolio_name || value;
            }}
          />
          {data.map((portfolio, idx) => (
            <Line
              key={portfolio.portfolio_id}
              type="monotone"
              dataKey={`portfolio_${idx}`}
              stroke={colors[idx % colors.length]}
              strokeWidth={2}
              dot={false}
              name={`portfolio_${idx}`}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ComparisonChart;