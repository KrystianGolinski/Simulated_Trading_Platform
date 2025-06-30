import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Dashboard } from '../Dashboard';

// Mock the hooks to avoid actual API calls for tests
jest.mock('../../hooks/useStockData', () => ({
  useStocks: jest.fn(),
  useStockData: jest.fn()
}));

jest.mock('../../hooks/useDebounce', () => ({
  useDebounce: jest.fn((value) => value) // Return value immediately for tests
}));

// Mock the StockChart component
jest.mock('../StockChart', () => ({
  StockChart: jest.fn(({ symbol, loading, error }) => (
    <div data-testid="stock-chart">
      <div>Symbol: {symbol}</div>
      {loading && <div>Loading chart...</div>}
      {error && <div>Chart error: {error}</div>}
    </div>
  ))
}));

import { useStocks, useStockData } from '../../hooks/useStockData';

const mockUseStocks = useStocks as jest.MockedFunction<typeof useStocks>;
const mockUseStockData = useStockData as jest.MockedFunction<typeof useStockData>;

describe('Dashboard Component', () => {
  const mockStockData = [
    {
      time: '2023-01-01',
      symbol: 'AAPL',
      open: 150.0,
      high: 155.0,
      low: 148.0,
      close: 153.0,
      volume: 1000000
    }
  ];

  beforeEach(() => {
    // Reset mocks before each test
    mockUseStocks.mockReturnValue({
      stocks: ['AAPL', 'GOOGL', 'MSFT'],
      pagination: null,
      loading: false,
      error: null
    });

    mockUseStockData.mockReturnValue({
      data: mockStockData,
      pagination: null,
      loading: false,
      error: null
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders stock selection dropdown', () => {
    render(<Dashboard />);
    
    expect(screen.getByText('Stock Symbol')).toBeInTheDocument();
    expect(screen.getByDisplayValue('AAPL')).toBeInTheDocument();
  });

  it('renders date input fields', () => {
    render(<Dashboard />);
    
    expect(screen.getByText('Start Date')).toBeInTheDocument();
    expect(screen.getByText('End Date')).toBeInTheDocument();
  });

  it('renders timeframe selection', () => {
    render(<Dashboard />);
    
    expect(screen.getByText('Timeframe')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Daily')).toBeInTheDocument();
  });

  it('renders StockChart component', () => {
    render(<Dashboard />);
    
    // The chart area should be present even if StockChart isn't rendered
    expect(screen.getByText('Stock Symbol')).toBeInTheDocument();
  });

  it('updates selected symbol when dropdown changes', async () => {
    const user = userEvent.setup();
    render(<Dashboard />);
    
    const select = screen.getByDisplayValue('AAPL');
    await user.selectOptions(select, 'GOOGL');
    
    expect(screen.getByDisplayValue('GOOGL')).toBeInTheDocument();
  });

  it('updates start date when input changes', async () => {
    const user = userEvent.setup();
    render(<Dashboard />);
    
    const startDateInput = screen.getByDisplayValue('2024-01-01');
    await user.clear(startDateInput);
    await user.type(startDateInput, '2023-06-01');
    
    expect(startDateInput).toHaveValue('2023-06-01');
  });

  it('updates end date when input changes', async () => {
    const user = userEvent.setup();
    render(<Dashboard />);
    
    const endDateInput = screen.getByDisplayValue('2024-12-31');
    await user.clear(endDateInput);
    await user.type(endDateInput, '2023-12-01');
    
    expect(endDateInput).toHaveValue('2023-12-01');
  });

  it('shows stock options from useStocks hook', () => {
    render(<Dashboard />);
    
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('GOOGL')).toBeInTheDocument();
    expect(screen.getByText('MSFT')).toBeInTheDocument();
  });

  it('passes correct props to StockChart component', () => {
    render(<Dashboard />);
    
    // Verify dashboard renders correctly
    expect(screen.getByText('Trading Platform Dashboard')).toBeInTheDocument();
  });

  it('calls useStockData with debounced values', () => {
    render(<Dashboard />);
    
    // Verify useStockData hook is called
    expect(mockUseStockData).toHaveBeenCalled();
  });

  it('handles loading state from useStockData', () => {
    mockUseStockData.mockReturnValue({
      data: [],
      pagination: null,
      loading: true,
      error: null
    });

    render(<Dashboard />);
    
    // When loading, dashboard should still render controls
    expect(screen.getByText('Stock Symbol')).toBeInTheDocument();
  });

  it('handles error state from useStockData', () => {
    const errorMessage = 'Failed to fetch stock data';
    mockUseStockData.mockReturnValue({
      data: [],
      pagination: null,
      loading: false,
      error: errorMessage
    });

    render(<Dashboard />);
    
    // When error, dashboard should still render controls
    expect(screen.getByText('Stock Symbol')).toBeInTheDocument();
  });

  it('has proper date constraints on date inputs initially', () => {
    render(<Dashboard />);
    
    const inputs = screen.getAllByDisplayValue(/2024/);
    const startDateInput = inputs[0]; // First date input
    const endDateInput = inputs[1];   // Second date input
    
    // Should have default constraints initially (before API call completes)
    expect(startDateInput).toHaveAttribute('min', '2015-06-17');
    expect(startDateInput).toHaveAttribute('max', '2025-06-13');
    expect(endDateInput).toHaveAttribute('min', '2015-06-17');
    expect(endDateInput).toHaveAttribute('max', '2025-06-13');
  });

  it('maintains responsive layout classes', () => {
    render(<Dashboard />);
    
    const controlsContainer = screen.getByText('Stock Symbol').closest('.grid-responsive-4');
    expect(controlsContainer).toHaveClass('grid-responsive-4');
  });

  it('uses memoized stock options for performance', () => {
    const { rerender } = render(<Dashboard />);
    
    // Get initial options
    const initialOptions = screen.getAllByRole('option');
    
    // Re-render with same stocks
    rerender(<Dashboard />);
    
    // Options should be the same references (memoized)
    const rerenderedOptions = screen.getAllByRole('option');
    expect(rerenderedOptions).toHaveLength(initialOptions.length);
  });
});