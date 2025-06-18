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
      <div className="p-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">No Results Available</h1>
          <p className="text-gray-600">Please run a simulation to see results.</p>
        </div>
      </div>
    );
  }

  // Handle cases where simulation failed or is incomplete
  if (results.status === 'failed') {
    return (
      <div className="p-6">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Simulation Failed</h1>
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <p className="text-red-700">{results.error_message || 'Unknown error occurred'}</p>
          </div>
          {onStartNew && (
            <button 
              onClick={onStartNew}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700"
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
      <div className="p-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Simulation In Progress</h1>
          <p className="text-gray-600">Status: {results.status}</p>
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
    <div className="p-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Simulation Results
        </h1>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
          <div className="bg-white rounded-lg shadow p-3">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
              Starting Capital
            </h3>
            <p className="text-2xl font-bold text-gray-900 mt-2">
              ${startingCapital.toLocaleString()}
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
              Final Value
            </h3>
            <p className="text-2xl font-bold text-gray-900 mt-2">
              ${finalPortfolioValue.toLocaleString()}
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
              Total Return
            </h3>
            <p className={`text-2xl font-bold mt-2 ${
              totalReturnPercentage >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {totalReturnPercentage >= 0 ? '+' : ''}{totalReturnPercentage.toFixed(2)}%
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wider">
              Profit/Loss
            </h3>
            <p className={`text-2xl font-bold mt-2 ${
              profitLoss >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {profitLoss >= 0 ? '+' : ''}${profitLoss.toLocaleString()}
            </p>
          </div>
        </div>

        {/* Equity Curve Chart */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="h-80">
            <Line ref={chartRef} data={chartData} options={chartOptions} />
          </div>
        </div>

        {/* Trading Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-lg font-semibold mb-4">Trading Statistics</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Trades:</span>
                <span className="font-semibold">{totalTrades}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Winning Trades:</span>
                <span className="font-semibold text-green-600">{winningTrades}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Losing Trades:</span>
                <span className="font-semibold text-red-600">{losingTrades}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Win Rate:</span>
                <span className="font-semibold">{winRate}%</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-lg font-semibold mb-4">Simulation Configuration</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Period:</span>
                <span className="font-semibold">{results.config.start_date} to {results.config.end_date}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Stocks:</span>
                <span className="font-semibold">{results.config.symbols.length} symbols</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Strategy:</span>
                <span className="font-semibold">{results.config.strategy}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Short MA:</span>
                <span className="font-semibold">{results.config.short_ma} days</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Long MA:</span>
                <span className="font-semibold">{results.config.long_ma} days</span>
              </div>
              <div className="mt-4">
                <span className="text-gray-600">Selected Stocks:</span>
                <div className="mt-1">
                  <span className="font-semibold">{results.config.symbols.join(', ')}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex space-x-4">
            {onStartNew && (
              <button 
                onClick={onStartNew}
                className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700"
              >
                Run New Simulation
              </button>
            )}
            <button className="bg-gray-600 text-white px-6 py-2 rounded-md hover:bg-gray-700">
              Export Results
            </button>
            <button className="bg-green-600 text-white px-6 py-2 rounded-md hover:bg-green-700">
              Save Simulation
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};