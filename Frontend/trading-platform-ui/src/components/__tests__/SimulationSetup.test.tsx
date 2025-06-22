import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SimulationSetup } from '../SimulationSetup';
import { apiService } from '../../services/api';

// Mock the hooks
jest.mock('../../hooks/useStockData', () => ({
  useStocks: jest.fn()
}));

// Mock the API service
jest.mock('../../services/api', () => ({
  apiService: {
    validateSimulation: jest.fn()
  }
}));

import { useStocks } from '../../hooks/useStockData';

const mockUseStocks = useStocks as jest.MockedFunction<typeof useStocks>;
const mockApiService = apiService as jest.Mocked<typeof apiService>;

describe('SimulationSetup Component', () => {
  const mockOnStartSimulation = jest.fn();
  const mockOnClearError = jest.fn();

  const defaultProps = {
    onStartSimulation: mockOnStartSimulation,
    isLoading: false,
    error: null,
    onClearError: mockOnClearError
  };

  beforeEach(() => {
    mockUseStocks.mockReturnValue({
      stocks: ['AAPL', 'GOOGL', 'MSFT', 'TSLA'],
      loading: false
    });

    mockApiService.validateSimulation.mockResolvedValue({
      is_valid: true,
      errors: [],
      warnings: []
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders simulation setup form', () => {
    render(<SimulationSetup {...defaultProps} />);
    
    expect(screen.getByRole('heading', { name: /simulation setup/i })).toBeInTheDocument();
  });

  it('renders stock selection checkboxes', () => {
    render(<SimulationSetup {...defaultProps} />);
    
    expect(screen.getByRole('checkbox', { name: /aapl/i })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /googl/i })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /msft/i })).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /tsla/i })).toBeInTheDocument();
  });

  it('renders configuration form fields', () => {
    render(<SimulationSetup {...defaultProps} />);
    
    expect(screen.getByText('Start Date')).toBeInTheDocument();
    expect(screen.getByText('End Date')).toBeInTheDocument();
    expect(screen.getByText('Starting Capital ($)')).toBeInTheDocument();
  });

  it('renders strategy-specific parameters for MA crossover', () => {
    render(<SimulationSetup {...defaultProps} />);
    
    // MA crossover is default strategy
    expect(screen.getByText('Short MA Period (days)')).toBeInTheDocument();
    expect(screen.getByText('Long MA Period (days)')).toBeInTheDocument();
  });

  it('allows selecting and deselecting stocks', async () => {
    const user = userEvent.setup();
    render(<SimulationSetup {...defaultProps} />);
    
    const aaplCheckbox = screen.getByRole('checkbox', { name: /aapl/i });
    
    // Initially unchecked
    expect(aaplCheckbox).not.toBeChecked();
    
    // Select AAPL
    await user.click(aaplCheckbox);
    expect(aaplCheckbox).toBeChecked();
    
    // Deselect AAPL
    await user.click(aaplCheckbox);
    expect(aaplCheckbox).not.toBeChecked();
  });

  it('updates form fields correctly', async () => {
    const user = userEvent.setup();
    render(<SimulationSetup {...defaultProps} />);
    
    // Update start date - find by current value
    const startDateInput = screen.getByDisplayValue('2023-01-01');
    await user.clear(startDateInput);
    await user.type(startDateInput, '2023-06-01');
    expect(startDateInput).toHaveValue('2023-06-01');
    
    // Update capital - find by current value
    const capitalInput = screen.getByDisplayValue('10000');
    await user.clear(capitalInput);
    await user.type(capitalInput, '25000');
    expect(capitalInput).toHaveValue(25000);
  });

  it('validates configuration before starting simulation', async () => {
    const user = userEvent.setup();
    render(<SimulationSetup {...defaultProps} />);
    
    // Select at least one stock
    await user.click(screen.getByRole('checkbox', { name: /aapl/i }));
    
    // Submit form
    const submitButton = screen.getByRole('button', { name: /start simulation/i });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockApiService.validateSimulation).toHaveBeenCalled();
    });
  });

  it('calls onStartSimulation when validation passes', async () => {
    const user = userEvent.setup();
    render(<SimulationSetup {...defaultProps} />);
    
    // Select a stock
    await user.click(screen.getByRole('checkbox', { name: /aapl/i }));
    
    // Submit form
    const submitButton = screen.getByRole('button', { name: /start simulation/i });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnStartSimulation).toHaveBeenCalledWith({
        symbols: ['AAPL'],
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        starting_capital: 10000,
        strategy: 'ma_crossover',
        short_ma: 20,
        long_ma: 50,
        rsi_period: 14,
        rsi_oversold: 30,
        rsi_overbought: 70
      });
    });
  });

  it('displays validation errors', async () => {
    const user = userEvent.setup();
    
    mockApiService.validateSimulation.mockResolvedValue({
      is_valid: false,
      errors: [
        {
          field: 'starting_capital',
          message: 'Capital must be at least $1000',
          error_code: 'CAPITAL_TOO_LOW'
        }
      ],
      warnings: []
    });
    
    render(<SimulationSetup {...defaultProps} />);
    
    await user.click(screen.getByRole('checkbox', { name: /aapl/i }));
    await user.click(screen.getByRole('button', { name: /start simulation/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/capital must be at least \$1000/i)).toBeInTheDocument();
    });
  });

  it('displays validation warnings', async () => {
    const user = userEvent.setup();
    
    mockApiService.validateSimulation.mockResolvedValue({
      is_valid: true,
      errors: [],
      warnings: ['Date range is longer than 5 years']
    });
    
    render(<SimulationSetup {...defaultProps} />);
    
    await user.click(screen.getByRole('checkbox', { name: /aapl/i }));
    await user.click(screen.getByRole('button', { name: /start simulation/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/date range is longer than 5 years/i)).toBeInTheDocument();
    });
  });

  it('shows loading state during validation', async () => {
    const user = userEvent.setup();
    
    // Make validation take time
    mockApiService.validateSimulation.mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({
        is_valid: true,
        errors: [],
        warnings: []
      }), 100))
    );
    
    render(<SimulationSetup {...defaultProps} />);
    
    await user.click(screen.getByRole('checkbox', { name: /aapl/i }));
    await user.click(screen.getByRole('button', { name: /start simulation/i }));
    
    expect(screen.getByText(/validating/i)).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.queryByText(/validating/i)).not.toBeInTheDocument();
    });
  });

  it('shows loading state when simulation is starting', () => {
    render(<SimulationSetup {...{ ...defaultProps, isLoading: true }} />);
    
    const submitButton = screen.getByRole('button', { name: /starting simulation/i });
    expect(submitButton).toBeDisabled();
  });

  it('displays error prop when provided', () => {
    const errorMessage = 'Simulation failed to start';
    render(<SimulationSetup {...{ ...defaultProps, error: errorMessage }} />);
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('clears error when onClearError is called', async () => {
    const user = userEvent.setup();
    const errorMessage = 'Previous error';
    
    render(<SimulationSetup {...{ ...defaultProps, error: errorMessage }} />);
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    
    // Interact with form to trigger error clearing
    await user.click(screen.getByRole('checkbox', { name: /aapl/i }));
    await user.click(screen.getByRole('button', { name: /start simulation/i }));
    
    expect(mockOnClearError).toHaveBeenCalled();
  });

  it('handles validation service unavailable', async () => {
    const user = userEvent.setup();
    
    // Mock API service error
    mockApiService.validateSimulation.mockRejectedValue(new Error('Service unavailable'));
    
    render(<SimulationSetup {...defaultProps} />);
    
    await user.click(screen.getByRole('checkbox', { name: /aapl/i }));
    await user.click(screen.getByRole('button', { name: /start simulation/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/validation service unavailable/i)).toBeInTheDocument();
    });
    
    expect(mockOnStartSimulation).not.toHaveBeenCalled();
  });

  it('shows loading state for stocks', () => {
    mockUseStocks.mockReturnValue({
      stocks: [],
      loading: true
    });
    
    render(<SimulationSetup {...defaultProps} />);

    expect(screen.getByText('Stock Selection')).toBeInTheDocument();
  });

  it('maintains form state when validation fails', async () => {
    const user = userEvent.setup();
    
    mockApiService.validateSimulation.mockResolvedValue({
      is_valid: false,
      errors: [{ field: 'general', message: 'Test error', error_code: 'TEST' }],
      warnings: []
    });
    
    render(<SimulationSetup {...defaultProps} />);
    
    // Set form values
    await user.click(screen.getByRole('checkbox', { name: /aapl/i }));
    const capitalInput = screen.getByDisplayValue('10000');
    await user.clear(capitalInput);
    await user.type(capitalInput, '15000');
    
    // Submit and fail validation
    await user.click(screen.getByRole('button', { name: /start simulation/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/test error/i)).toBeInTheDocument();
    });
    
    // Form values should be preserved
    expect(screen.getByRole('checkbox', { name: /aapl/i })).toBeChecked();
    expect(capitalInput).toHaveValue(15000);
  });
});