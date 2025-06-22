import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SimulationResults } from '../SimulationResults';
import { SimulationResults as SimulationResultsType } from '../../services/api';

// Mock Chart.js
jest.mock('react-chartjs-2', () => ({
  Line: () => <div data-testid="equity-curve-chart">Mocked Chart</div>
}));

// Mock chartjs-adapter-date-fns
jest.mock('chartjs-adapter-date-fns', () => ({}));

describe('SimulationResults Component', () => {
  const mockOnStartNew = jest.fn();

  const mockSuccessfulResults: SimulationResultsType = {
    simulation_id: 'sim123',
    status: 'completed',
    starting_capital: 10000,
    ending_value: 12500,
    total_return_pct: 25.0,
    performance_metrics: {
      total_return_pct: 25.0,
      total_trades: 42,
      winning_trades: 28,
      losing_trades: 14,
      max_drawdown_pct: -5.2,
      sharpe_ratio: 1.35,
      win_rate: 66.7
    },
    equity_curve: [
      { date: '2023-01-01', value: 10000 },
      { date: '2023-06-01', value: 11000 },
      { date: '2023-12-31', value: 12500 }
    ],
    config: {
      symbols: ['AAPL', 'GOOGL', 'MSFT'],
      start_date: '2023-01-01',
      end_date: '2023-12-31',
      starting_capital: 10000,
      strategy: 'ma_crossover',
      short_ma: 20,
      long_ma: 50
    },
    created_at: '2023-01-01T00:00:00Z'
  };

  const mockFailedResults: SimulationResultsType = {
    ...mockSuccessfulResults,
    status: 'failed',
    error_message: 'Insufficient data for analysis'
  };

  const mockInProgressResults: SimulationResultsType = {
    ...mockSuccessfulResults,
    status: 'running'
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders no results state when results is null', () => {
    render(<SimulationResults results={null} onStartNew={mockOnStartNew} />);
    
    expect(screen.getByText('No Results Available')).toBeInTheDocument();
    expect(screen.getByText('Please run a simulation to see results.')).toBeInTheDocument();
  });

  it('renders failed simulation state', () => {
    render(<SimulationResults results={mockFailedResults} onStartNew={mockOnStartNew} />);
    
    expect(screen.getByText('Simulation Failed')).toBeInTheDocument();
    expect(screen.getByText('Insufficient data for analysis')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /try new simulation/i })).toBeInTheDocument();
  });

  it('renders failed simulation without error message', () => {
    const failedWithoutMessage = { ...mockFailedResults, error_message: undefined };
    render(<SimulationResults results={failedWithoutMessage} onStartNew={mockOnStartNew} />);
    
    expect(screen.getByText('Unknown error occurred')).toBeInTheDocument();
  });

  it('renders in progress simulation state', () => {
    render(<SimulationResults results={mockInProgressResults} onStartNew={mockOnStartNew} />);
    
    expect(screen.getByText('Simulation In Progress')).toBeInTheDocument();
    expect(screen.getByText('Status: running')).toBeInTheDocument();
  });

  it('renders successful simulation results', () => {
    render(<SimulationResults results={mockSuccessfulResults} onStartNew={mockOnStartNew} />);
    
    expect(screen.getByText('Simulation Results')).toBeInTheDocument();
    expect(screen.getByText('$10,000')).toBeInTheDocument(); // Starting capital
    expect(screen.getByText('$12,500')).toBeInTheDocument(); // Final value
    expect(screen.getByText('+25.00%')).toBeInTheDocument(); // Total return
    expect(screen.getByText('+$2,500')).toBeInTheDocument(); // Profit/loss
  });

  it('displays key metrics correctly', () => {
    render(<SimulationResults results={mockSuccessfulResults} onStartNew={mockOnStartNew} />);
    
    expect(screen.getByText('Starting Capital')).toBeInTheDocument();
    expect(screen.getByText('Final Value')).toBeInTheDocument();
    expect(screen.getByText('Total Return')).toBeInTheDocument();
    expect(screen.getByText('Profit/Loss')).toBeInTheDocument();
  });

  it('displays positive returns in green', () => {
    render(<SimulationResults results={mockSuccessfulResults} onStartNew={mockOnStartNew} />);
    
    const totalReturn = screen.getByText('+25.00%');
    const profitLoss = screen.getByText('+$2,500');
    
    expect(totalReturn).toHaveClass('text-profit');
    expect(profitLoss).toHaveClass('text-profit');
  });

  it('displays negative returns in red', () => {
    const lossResults = {
      ...mockSuccessfulResults,
      ending_value: 8000,
      total_return_pct: -20.0
    };
    
    render(<SimulationResults results={lossResults} onStartNew={mockOnStartNew} />);
    
    const totalReturn = screen.getByText('-20.00%');
    const profitLoss = screen.getByText(/\$-2,000/); // Comma formatting RegEx
    
    expect(totalReturn).toHaveClass('text-loss');
    expect(profitLoss).toHaveClass('text-loss');
  });

  it('renders equity curve chart', () => {
    render(<SimulationResults results={mockSuccessfulResults} onStartNew={mockOnStartNew} />);
    
    expect(screen.getByTestId('equity-curve-chart')).toBeInTheDocument();
  });

  it('displays trading statistics', () => {
    render(<SimulationResults results={mockSuccessfulResults} onStartNew={mockOnStartNew} />);
    
    expect(screen.getByText('Trading Statistics')).toBeInTheDocument();
    expect(screen.getByText('Total Trades:')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('Winning Trades:')).toBeInTheDocument();
    expect(screen.getByText('28')).toBeInTheDocument();
    expect(screen.getByText('Losing Trades:')).toBeInTheDocument();
    expect(screen.getByText('14')).toBeInTheDocument();
    expect(screen.getByText('Win Rate:')).toBeInTheDocument();
    expect(screen.getByText('66.7%')).toBeInTheDocument();
  });

  it('calculates win rate correctly', () => {
    const customResults = {
      ...mockSuccessfulResults,
      performance_metrics: {
        total_return_pct: 25.0,
        total_trades: 100,
        winning_trades: 65,
        losing_trades: 35,
        max_drawdown_pct: -5.2,
        win_rate: 65.0
      }
    };
    
    render(<SimulationResults results={customResults} onStartNew={mockOnStartNew} />);
    
    expect(screen.getByText('65.0%')).toBeInTheDocument();
  });

  it('handles zero trades gracefully', () => {
    const noTradesResults = {
      ...mockSuccessfulResults,
      performance_metrics: {
        total_return_pct: 0,
        total_trades: 0,
        winning_trades: 0,
        losing_trades: 0,
        max_drawdown_pct: 0,
        win_rate: 0
      }
    };
    
    render(<SimulationResults results={noTradesResults} onStartNew={mockOnStartNew} />);
    
    expect(screen.getByText('Total Trades:')).toBeInTheDocument();
    expect(screen.getByText('Win Rate:')).toBeInTheDocument();
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('displays simulation configuration', () => {
    render(<SimulationResults results={mockSuccessfulResults} onStartNew={mockOnStartNew} />);
    
    expect(screen.getByText('Simulation Configuration')).toBeInTheDocument();
    expect(screen.getByText('2023-01-01 to 2023-12-31')).toBeInTheDocument();
    expect(screen.getByText('3 symbols')).toBeInTheDocument();
    expect(screen.getByText('ma_crossover')).toBeInTheDocument();
    expect(screen.getByText('20 days')).toBeInTheDocument();
    expect(screen.getByText('50 days')).toBeInTheDocument();
    expect(screen.getByText('AAPL, GOOGL, MSFT')).toBeInTheDocument();
  });

  it('renders action buttons', () => {
    render(<SimulationResults results={mockSuccessfulResults} onStartNew={mockOnStartNew} />);
    
    expect(screen.getByRole('button', { name: /run new simulation/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /export results/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /save simulation/i })).toBeInTheDocument();
  });

  it('calls onStartNew when button is clicked', async () => {
    render(<SimulationResults results={mockSuccessfulResults} onStartNew={mockOnStartNew} />);
    
    const newSimButton = screen.getByRole('button', { name: /run new simulation/i });
    await userEvent.click(newSimButton);
    
    expect(mockOnStartNew).toHaveBeenCalledTimes(1);
  });

  it('does not render new simulation button when onStartNew is not provided', () => {
    render(<SimulationResults results={mockSuccessfulResults} />);
    
    expect(screen.queryByRole('button', { name: /run new simulation/i })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /export results/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /save simulation/i })).toBeInTheDocument();
  });

  it('handles missing performance metrics gracefully', () => {
    const resultsWithoutMetrics = {
      ...mockSuccessfulResults,
      performance_metrics: undefined
    };
    
    render(<SimulationResults results={resultsWithoutMetrics} onStartNew={mockOnStartNew} />);
    
    // Check that trading statistics section exists even without metrics
    expect(screen.getByText('Trading Statistics')).toBeInTheDocument();
    expect(screen.getByText('Total Trades:')).toBeInTheDocument();
    expect(screen.getByText('Win Rate:')).toBeInTheDocument();
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('handles missing equity curve gracefully', () => {
    const resultsWithoutCurve = {
      ...mockSuccessfulResults,
      equity_curve: undefined
    };
    
    render(<SimulationResults results={resultsWithoutCurve} onStartNew={mockOnStartNew} />);
    
    // Should still render the chart component even with empty data
    expect(screen.getByTestId('equity-curve-chart')).toBeInTheDocument();
  });

  it('handles missing ending value gracefully', () => {
    const resultsWithoutEndingValue = {
      ...mockSuccessfulResults,
      ending_value: undefined
    };
    
    render(<SimulationResults results={resultsWithoutEndingValue} onStartNew={mockOnStartNew} />);
    
    // Should default to starting capital
    expect(screen.getByText('Final Value')).toBeInTheDocument();
    expect(screen.getAllByText(/\$10,000/)).toHaveLength(2); // Both starting and final should be 10k
  });

  it('formats large numbers correctly', () => {
    const largeResults = {
      ...mockSuccessfulResults,
      starting_capital: 1000000,
      ending_value: 1250000
    };
    
    render(<SimulationResults results={largeResults} onStartNew={mockOnStartNew} />);
    
    expect(screen.getByText('$1,000,000')).toBeInTheDocument();
    expect(screen.getByText('$1,250,000')).toBeInTheDocument();
    expect(screen.getByText('+$250,000')).toBeInTheDocument();
  });

  it('displays winning trades in green and losing trades in red', () => {
    render(<SimulationResults results={mockSuccessfulResults} onStartNew={mockOnStartNew} />);
    
    const winningTrades = screen.getByText('28');
    const losingTrades = screen.getByText('14');
    
    expect(winningTrades).toHaveClass('text-profit');
    expect(losingTrades).toHaveClass('text-loss');
  });

  it('calls onStartNew from failed state', async () => {
    render(<SimulationResults results={mockFailedResults} onStartNew={mockOnStartNew} />);
    
    const tryNewButton = screen.getByRole('button', { name: /try new simulation/i });
    await userEvent.click(tryNewButton);
    
    expect(mockOnStartNew).toHaveBeenCalledTimes(1);
  });

  it('does not render try new button in failed state when onStartNew is not provided', () => {
    render(<SimulationResults results={mockFailedResults} />);
    
    expect(screen.queryByRole('button', { name: /try new simulation/i })).not.toBeInTheDocument();
  });

  it('handles edge case of zero starting capital', () => {
    const zeroCapitalResults = {
      ...mockSuccessfulResults,
      starting_capital: 0,
      ending_value: 1000
    };
    
    render(<SimulationResults results={zeroCapitalResults} onStartNew={mockOnStartNew} />);
    
    expect(screen.getByText('$0')).toBeInTheDocument();
    expect(screen.getByText('$1,000')).toBeInTheDocument();
  });
});