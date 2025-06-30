import { Line } from 'react-chartjs-2';
import 'chartjs-adapter-date-fns';
import { SimulationResults as SimulationResultsType } from '../services/api';

interface SimulationResultsProps {
  results: SimulationResultsType | null;
  onStartNew?: () => void;
}

export const SimulationResults: React.FC<SimulationResultsProps> = ({ 
  results, 
  onStartNew 
}) => {

  if (!results) {
    return (
      <div style={{ padding: '12px' }}>
        <div style={{ maxWidth: '900px', margin: '0 auto', textAlign: 'center' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem', color: '#111827' }}>
            No Results Available
          </h1>
          <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '24px', boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)' }}>
            <p style={{ color: '#6b7280', fontSize: '1rem' }}>Please run a simulation to see results.</p>
          </div>
        </div>
      </div>
    );
  }

  // Handle cases where simulation failed or is incomplete
  if (results.status === 'failed') {
    return (
      <div style={{ padding: '12px' }}>
        <div style={{ maxWidth: '900px', margin: '0 auto', textAlign: 'center' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem', color: '#111827' }}>
            Simulation Failed
          </h1>
          <div style={{ backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', padding: '16px', marginBottom: '1.5rem' }}>
            <p style={{ color: '#dc2626', fontSize: '1rem' }}>
              {results.error_message || 'Unknown error occurred'}
            </p>
          </div>
          {onStartNew && (
            <button 
              onClick={onStartNew}
              style={{
                backgroundColor: '#2563eb',
                color: 'white',
                padding: '8px 16px',
                borderRadius: '6px',
                border: 'none',
                fontSize: '14px',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              Try New Simulation
            </button>
          )}
        </div>
      </div>
    );
  }

  if (results.status !== 'completed') {
    return (
      <div style={{ padding: '12px' }}>
        <div style={{ maxWidth: '900px', margin: '0 auto', textAlign: 'center' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem', color: '#111827' }}>
            Simulation In Progress
          </h1>
          <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '24px', boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)' }}>
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ width: '100%', height: '8px', backgroundColor: '#e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{ 
                  width: '60%', 
                  height: '100%', 
                  backgroundColor: '#3b82f6', 
                  borderRadius: '4px',
                  animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite'
                }}></div>
              </div>
            </div>
            <p style={{ color: '#374151', fontSize: '1rem', fontWeight: '500', marginBottom: '0.5rem' }}>
              Processing your simulation...
            </p>
            <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>
              Status: <span style={{ fontWeight: '600', textTransform: 'capitalize' }}>{results.status}</span>
            </p>
          </div>
        </div>
      </div>
    );
  }

  const startingCapital = results.starting_capital || 0;
  const finalPortfolioValue = results.ending_value || startingCapital;
  const totalReturnPercentage = results.total_return_pct || 0;
  const performanceMetrics = results.performance_metrics;
  const totalTrades = performanceMetrics?.total_trades || 0;
  const winningTrades = performanceMetrics?.winning_trades || 0;
  const losingTrades = performanceMetrics?.losing_trades || 0;
  const equityCurve = results.equity_curve || [];

  const winRate = totalTrades > 0 ? ((winningTrades / totalTrades) * 100).toFixed(1) : '0';
  const profitLoss = finalPortfolioValue - startingCapital;

  // Equity Curve Chart Data
  const chartData = {
    labels: equityCurve.map(point => new Date(point.date)),
    datasets: [
      {
        label: 'Portfolio Value',
        data: equityCurve.map(point => ({ x: new Date(point.date), y: point.value })),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 6,
      }
    ],
  };

  const chartOptions = {
    responsive: true,
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
        text: 'Portfolio Equity Curve',
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          displayFormats: {
            day: 'MMM dd',
            month: 'MMM yyyy'
          }
        }
      },
      y: {
        type: 'linear' as const,
        title: {
          display: true,
          text: 'Portfolio Value ($)'
        },
        ticks: {
          callback: function(value: any) {
            return '$' + value.toLocaleString();
          }
        }
      },
    },
  };

  return (
    <div style={{ padding: '12px' }}>
      <div style={{ maxWidth: '900px', margin: '0 auto', textAlign: 'center' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '1rem', color: '#111827' }}>
          Simulation Results
        </h1>

        {/* Top Sections Row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
          {/* Performance Summary */}
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>Performance Summary</h2>
            <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '16px', boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Starting Capital:</span>
                  <span style={{ fontWeight: '600' }}>${startingCapital.toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Final Value:</span>
                  <span style={{ fontWeight: '600' }}>${finalPortfolioValue.toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Total Return:</span>
                  <span style={{ 
                    fontWeight: '600', 
                    color: totalReturnPercentage >= 0 ? '#059669' : '#dc2626' 
                  }}>
                    {totalReturnPercentage >= 0 ? '+' : ''}{totalReturnPercentage.toFixed(2)}%
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Profit/Loss:</span>
                  <span style={{ 
                    fontWeight: '600', 
                    color: profitLoss >= 0 ? '#059669' : '#dc2626' 
                  }}>
                    {profitLoss >= 0 ? '+' : ''}${profitLoss.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Trading Statistics */}
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>Trading Statistics</h2>
            <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '16px', boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Total Trades:</span>
                  <span style={{ fontWeight: '600' }}>{totalTrades}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Winning Trades:</span>
                  <span style={{ fontWeight: '600', color: '#059669' }}>{winningTrades}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Losing Trades:</span>
                  <span style={{ fontWeight: '600', color: '#dc2626' }}>{losingTrades}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Win Rate:</span>
                  <span style={{ fontWeight: '600' }}>{winRate}%</span>
                </div>
                {performanceMetrics?.profit_factor && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Profit Factor:</span>
                    <span style={{ fontWeight: '600', color: performanceMetrics.profit_factor >= 1 ? '#059669' : '#dc2626' }}>
                      {performanceMetrics.profit_factor.toFixed(2)}
                    </span>
                  </div>
                )}
                {performanceMetrics?.average_win && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Average Win:</span>
                    <span style={{ fontWeight: '600', color: '#059669' }}>
                      ${performanceMetrics.average_win.toFixed(2)}
                    </span>
                  </div>
                )}
                {performanceMetrics?.average_loss && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Average Loss:</span>
                    <span style={{ fontWeight: '600', color: '#dc2626' }}>
                      ${performanceMetrics.average_loss.toFixed(2)}
                    </span>
                  </div>
                )}
                {performanceMetrics?.annualized_return && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Annualised Return:</span>
                    <span style={{ 
                      fontWeight: '600', 
                      color: performanceMetrics.annualized_return >= 0 ? '#059669' : '#dc2626' 
                    }}>
                      {performanceMetrics.annualized_return >= 0 ? '+' : ''}{performanceMetrics.annualized_return.toFixed(2)}%
                    </span>
                  </div>
                )}
                {performanceMetrics?.volatility && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Volatility:</span>
                    <span style={{ fontWeight: '600' }}>{performanceMetrics.volatility.toFixed(2)}%</span>
                  </div>
                )}
                {performanceMetrics?.sharpe_ratio && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Sharpe Ratio:</span>
                    <span style={{ 
                      fontWeight: '600',
                      color: performanceMetrics.sharpe_ratio >= 1 ? '#059669' : performanceMetrics.sharpe_ratio >= 0 ? '#d97706' : '#dc2626'
                    }}>
                      {performanceMetrics.sharpe_ratio.toFixed(2)}
                    </span>
                  </div>
                )}
                {performanceMetrics?.max_drawdown_pct && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Max Drawdown:</span>
                    <span style={{ fontWeight: '600', color: '#dc2626' }}>
                      {performanceMetrics.max_drawdown_pct.toFixed(2)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Configuration */}
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>Configuration</h2>
            <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '16px', boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Strategy:</span>
                  <span style={{ fontWeight: '600' }}>{results.config.strategy}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Stocks:</span>
                  <span style={{ fontWeight: '600' }}>{results.config.symbols.length} symbols</span>
                </div>
                {results.config.strategy === 'ma_crossover' && (
                  <>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Short MA:</span>
                      <span style={{ fontWeight: '600' }}>{results.config.strategy_parameters.short_ma} days</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Long MA:</span>
                      <span style={{ fontWeight: '600' }}>{results.config.strategy_parameters.long_ma} days</span>
                    </div>
                  </>
                )}
                {results.config.strategy === 'rsi' && (
                  <>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>RSI Period:</span>
                      <span style={{ fontWeight: '600' }}>{results.config.strategy_parameters.rsi_period} days</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Oversold:</span>
                      <span style={{ fontWeight: '600' }}>{results.config.strategy_parameters.rsi_oversold}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: '#6b7280', fontSize: '0.875rem' }}>Overbought:</span>
                      <span style={{ fontWeight: '600' }}>{results.config.strategy_parameters.rsi_overbought}</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Chart */}
        <div style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151', textAlign: 'center' }}>Portfolio Growth</h2>
          <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '16px', boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)', height: '400px' }}>
            <div style={{ height: '100%' }}>
              <Line data={chartData} options={chartOptions} />
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem', color: '#374151' }}>Actions</h2>
          <div style={{ backgroundColor: 'white', borderRadius: '8px', padding: '16px', boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}>
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
                {onStartNew && (
                  <button 
                    onClick={onStartNew}
                    style={{
                      backgroundColor: '#2563eb',
                      color: 'white',
                      padding: '8px 16px',
                      borderRadius: '6px',
                      border: 'none',
                      fontSize: '14px',
                      fontWeight: '500',
                      cursor: 'pointer'
                    }}
                  >
                    Run New Simulation
                  </button>
                )}
                <button 
                  style={{
                    backgroundColor: '#6b7280',
                    color: 'white',
                    padding: '8px 16px',
                    borderRadius: '6px',
                    border: 'none',
                    fontSize: '14px',
                    fontWeight: '500',
                    cursor: 'pointer'
                  }}
                >
                  Export Results
                </button>
                <button 
                  style={{
                    backgroundColor: '#059669',
                    color: 'white',
                    padding: '8px 16px',
                    borderRadius: '6px',
                    border: 'none',
                    fontSize: '14px',
                    fontWeight: '500',
                    cursor: 'pointer'
                  }}
                >
                  Save Simulation
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};