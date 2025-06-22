import React, { useRef, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import 'chartjs-adapter-date-fns';
import { SimulationResults as SimulationResultsType } from '../services/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

interface SimulationResultsProps {
  results: SimulationResultsType | null;
  onStartNew?: () => void;
}

export const SimulationResults: React.FC<SimulationResultsProps> = ({ 
  results, 
  onStartNew 
}) => {
  const chartRef = useRef(null);

  useEffect(() => {
    const chart = chartRef.current;
    return () => {
      if (chart) {
        (chart as any).destroy();
      }
    };
  }, []);

  if (!results) {
    return (
      <div className="container-md text-center">
          <h1 className="page-title">No Results Available</h1>
          <p className="text-gray-600">Please run a simulation to see results.</p>
      </div>
    );
  }

  // Handle cases where simulation failed or is incomplete
  if (results.status === 'failed') {
    return (
      <div className="container-md">
          <h1 className="page-title">Simulation Failed</h1>
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <p className="text-red-700">{results.error_message || 'Unknown error occurred'}</p>
          </div>
          {onStartNew && (
            <button 
              onClick={onStartNew}
              className="btn-primary"
            >
              Try New Simulation
            </button>
          )}
      </div>
    );
  }

  if (results.status !== 'completed') {
    return (
      <div className="container-md text-center">
          <h1 className="page-title">Simulation In Progress</h1>
          <p className="text-gray-600">Status: {results.status}</p>
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
      }
    ],
  };

  const chartOptions = {
    responsive: true,
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
    <div className="container-xl py-4">
      <h1 className="page-title">
        Simulation Results
      </h1>

      {/* Key Metrics */}
      <div className="grid-responsive-4 mb-4">
        <div className="card-4">
          <h3 className="metric-header">
            Starting Capital
          </h3>
          <p className="metric-value text-gray-900 mt-1">
            ${startingCapital.toLocaleString()}
          </p>
        </div>
        
        <div className="card-4">
          <h3 className="metric-header">
            Final Value
          </h3>
          <p className="metric-value text-gray-900 mt-1">
            ${finalPortfolioValue.toLocaleString()}
          </p>
        </div>
        
        <div className="card-4">
          <h3 className="metric-header">
            Total Return
          </h3>
          <p className={`metric-value mt-1 ${
            totalReturnPercentage >= 0 ? 'text-profit' : 'text-loss'
          }`}>
            {totalReturnPercentage >= 0 ? '+' : ''}{totalReturnPercentage.toFixed(2)}%
          </p>
        </div>
        
        <div className="card-4">
          <h3 className="metric-header">
            Profit/Loss
          </h3>
          <p className={`metric-value mt-1 ${
            profitLoss >= 0 ? 'text-profit' : 'text-loss'
          }`}>
            {profitLoss >= 0 ? '+' : ''}${profitLoss.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Equity Curve Chart */}
      <div className="card-4 mb-4">
        <div className="chart-container">
          <Line ref={chartRef} data={chartData} options={chartOptions} />
        </div>
      </div>

      {/* Trading Statistics and Configuration */}
      <div className="grid-metrics mb-4">
        <div className="card-4">
          <h3 className="section-title">Trading Statistics</h3>
          <div className="space-y-2">
            <div className="flex-between">
              <span className="text-gray-600">Total Trades:</span>
              <span className="font-semibold">{totalTrades}</span>
            </div>
            <div className="flex-between">
              <span className="text-gray-600">Winning Trades:</span>
              <span className="font-semibold text-profit">{winningTrades}</span>
            </div>
            <div className="flex-between">
              <span className="text-gray-600">Losing Trades:</span>
              <span className="font-semibold text-loss">{losingTrades}</span>
            </div>
            <div className="flex-between">
              <span className="text-gray-600">Win Rate:</span>
              <span className="font-semibold">{winRate}%</span>
            </div>
          </div>
        </div>

        <div className="card-4">
          <h3 className="section-title">Simulation Configuration</h3>
          <div className="space-y-2">
            <div className="flex-between">
              <span className="text-gray-600">Period:</span>
              <span className="font-semibold text-sm">{results.config.start_date} to {results.config.end_date}</span>
            </div>
            <div className="flex-between">
              <span className="text-gray-600">Stocks:</span>
              <span className="font-semibold">{results.config.symbols.length} symbols</span>
            </div>
            <div className="flex-between">
              <span className="text-gray-600">Strategy:</span>
              <span className="font-semibold">{results.config.strategy}</span>
            </div>
            <div className="flex-between">
              <span className="text-gray-600">Short MA:</span>
              <span className="font-semibold">{results.config.short_ma} days</span>
            </div>
            <div className="flex-between">
              <span className="text-gray-600">Long MA:</span>
              <span className="font-semibold">{results.config.long_ma} days</span>
            </div>
            <div className="mt-3">
              <span className="text-gray-600">Selected Stocks:</span>
              <div className="mt-1">
                <span className="font-semibold text-sm">{results.config.symbols.join(', ')}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="card-4">
        <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
          {onStartNew && (
            <button 
              onClick={onStartNew}
              className="btn-primary"
            >
              Run New Simulation
            </button>
          )}
          <button className="btn-secondary">
            Export Results
          </button>
          <button className="btn-success">
            Save Simulation
          </button>
        </div>
      </div>
    </div>
  );
};