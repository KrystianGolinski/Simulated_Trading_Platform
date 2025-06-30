import { Line } from 'react-chartjs-2';
import 'chartjs-adapter-date-fns';
import { StockData } from '../services/api';

type ChartType = 'line' | 'candlestick' | 'ohlc';

interface StockChartProps {
  data: StockData[];
  symbol: string;
  loading: boolean;
  error: string | null;
  chartType?: ChartType;
  showVolume?: boolean;
}

export const StockChart: React.FC<StockChartProps> = ({ 
  data, 
  symbol, 
  loading, 
  error,
  chartType = 'line',
  showVolume = false // Will be used for volume charts later
}) => {
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        Error: {error}
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        No data available for the selected period
      </div>
    );
  }



  // Use data as-is for daily charts
  const processedData = data;

  // Prepare data based on chart type
  const getChartData = (): any => {
    if (chartType === 'line') {
      return {
        datasets: [
          {
            label: `${symbol} Close Price`,
            data: processedData.map(d => ({ x: new Date(d.time), y: d.close })),
            borderColor: 'rgb(59, 130, 246)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderWidth: 1,
            fill: false,
            tension: 0,
            pointRadius: 0,
          }
        ],
      };
    } else {
      // For candlestick and OHLC, show close price with volume-based coloring
      const candlestickData = processedData.map(d => {
        const prevClose = processedData[processedData.indexOf(d) - 1]?.close || d.open;
        const isUp = d.close > prevClose;
        
        return {
          x: new Date(d.time),
          y: d.close,
          borderColor: isUp ? 'rgb(34, 197, 94)' : 'rgb(239, 68, 68)',
          backgroundColor: isUp ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
        };
      });

      return {
        datasets: [
          {
            label: `${symbol} Price Movement`,
            data: candlestickData,
            borderColor: candlestickData.map(d => d.borderColor),
            backgroundColor: candlestickData.map(d => d.backgroundColor),
            borderWidth: 1,
            fill: false,
            pointRadius: 0,
            segment: {
              borderColor: (ctx: any) => {
                const current = processedData[ctx.p1DataIndex];
                const previous = processedData[ctx.p0DataIndex];
                return current && previous && current.close > previous.close ? 
                  'rgb(34, 197, 94)' : 'rgb(239, 68, 68)';
              }
            }
          }
        ],
      };
    }
  };

  const chartData: any = getChartData();

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
      duration: 750 // Smooth animations for daily data
    },
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: `${symbol} Stock Price ${chartType === 'line' ? '(Close)' : chartType === 'candlestick' ? '(High-Low with Close)' : '(OHLC Style)'}`,
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            const dataIndex = context.dataIndex;
            const dataPoint = processedData[dataIndex];
            
            if (chartType === 'line') {
              return `Close: $${context.parsed.y.toFixed(2)}`;
            } else if (dataPoint) {
              return [
                `Open: $${dataPoint.open.toFixed(2)}`,
                `High: $${dataPoint.high.toFixed(2)}`,
                `Low: $${dataPoint.low.toFixed(2)}`,
                `Close: $${dataPoint.close.toFixed(2)}`,
                `Volume: ${dataPoint.volume.toLocaleString()}`
              ];
            }
            return `Close: $${context.parsed.y.toFixed(2)}`;
          }
        }
      }
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          displayFormats: {
            millisecond: 'HH:mm:ss.SSS',
            second: 'HH:mm:ss',
            minute: 'HH:mm',
            hour: 'MMM dd HH:mm',
            day: 'MMM dd',
            week: 'MMM dd',
            month: 'MMM yyyy',
            quarter: 'MMM yyyy',
            year: 'yyyy'
          }
        },
        title: {
          display: true,
          text: 'Trading Time'
        },
        ticks: {
          maxTicksLimit: 10
        }
      },
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        title: {
          display: true,
          text: 'Price ($)'
        }
      },
    },
  };

  // Volume chart data - only prepare when needed
  const volumeChartData = showVolume ? {
    datasets: [
      {
        label: `${symbol} Volume`,
        data: processedData.map(d => ({ x: new Date(d.time), y: d.volume })),
        backgroundColor: 'rgba(107, 114, 128, 0.6)',
        borderColor: 'rgba(107, 114, 128, 0.8)',
        borderWidth: 0,
        pointRadius: 0,
      }
    ],
  } : null;

  const volumeOptions = showVolume ? {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        display: false,
      },
      y: {
        type: 'linear' as const,
        title: {
          display: true,
          text: 'Volume'
        }
      },
    },
  } : null;

  const renderChart = () => {
    // All chart types use Line component for now since we removed the financial package
    return <Line data={chartData} options={options as any} />;
  };

  return (
    <div className="w-full" style={{ padding: '16px' }}>
      {/* Main price chart */}
      <div style={{ height: showVolume ? '400px' : '600px', marginBottom: showVolume ? '16px' : '0' }}>
        {renderChart()}
      </div>
      
      {/* Volume chart */}
      {showVolume && volumeChartData && volumeOptions && (
        <div style={{ height: '150px' }}>
          <Line data={volumeChartData} options={volumeOptions} />
        </div>
      )}
    </div>
  );
};