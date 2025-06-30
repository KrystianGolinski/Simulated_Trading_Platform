import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SimulationProgress } from '../SimulationProgress';

describe('SimulationProgress Component', () => {
  const defaultProps = {
    isRunning: true,
    progress: 25,
    currentStep: 'Loading historical data'
  };

  it('renders nothing when simulation is not running', () => {
    const { container } = render(
      <SimulationProgress {...defaultProps} isRunning={false} />
    );
    
    expect(container.firstChild).toBeNull();
  });

  it('displays progress bar with correct width', () => {
    render(<SimulationProgress {...defaultProps} progress={75} />);
    
    const progressBar = document.querySelector('.bg-blue-600');
    expect(progressBar).toHaveStyle({ width: '75%' });
  });

  it('displays elapsed time when provided', () => {
    render(<SimulationProgress {...defaultProps} elapsedTime={120} />);
    
    expect(screen.getByText('Elapsed time: 120 seconds')).toBeInTheDocument();
  });

  it('displays estimated remaining time when provided', () => {
    render(<SimulationProgress {...defaultProps} estimatedRemaining={45.7} />);
    
    expect(screen.getByText('Estimated time remaining: 46 seconds')).toBeInTheDocument();
  });

  it('displays simulation ID when provided', () => {
    const fullId = 'abc123def456ghi789';
    render(<SimulationProgress {...defaultProps} simulationId={fullId} />);
    
    expect(screen.getByText('Simulation ID: abc123de...')).toBeInTheDocument();
  });

  it('renders loading spinner', () => {
    render(<SimulationProgress {...defaultProps} />);
    
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass('animate-spin');
  });

  it('renders cancel button when onCancel is provided', () => {
    const mockOnCancel = jest.fn();
    render(<SimulationProgress {...defaultProps} onCancel={mockOnCancel} />);
    
    expect(screen.getByRole('button', { name: /cancel simulation/i })).toBeInTheDocument();
  });

  it('does not render cancel button when onCancel is not provided', () => {
    render(<SimulationProgress {...defaultProps} />);
    
    expect(screen.queryByRole('button', { name: /cancel simulation/i })).not.toBeInTheDocument();
  });

  it('calls onCancel when cancel button is clicked', async () => {
    const mockOnCancel = jest.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    
    render(<SimulationProgress {...defaultProps} onCancel={mockOnCancel} />);
    
    const cancelButton = screen.getByRole('button', { name: /cancel simulation/i });
    await user.click(cancelButton);
    
    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('shows completed steps with green styling', () => {
    render(<SimulationProgress {...defaultProps} progress={50} currentStep="Executing trades" />);
    
    // First two steps should be completed (progress 50% means ~3 steps completed)
    const completedStep = screen.getByText('Initializing simulation engine');
    expect(completedStep).toHaveClass('text-green-600');
  });

  it('shows pending steps with gray styling', () => {
    render(<SimulationProgress {...defaultProps} progress={25} currentStep="Loading historical data" />);
    
    const pendingStep = screen.getByText('Generating results');
    expect(pendingStep).toHaveClass('text-gray-500');
  });

  it('handles 0% progress correctly', () => {
    render(<SimulationProgress {...defaultProps} progress={0} />);
    
    expect(screen.getByText('0%')).toBeInTheDocument();
    const progressBar = document.querySelector('.bg-blue-600');
    expect(progressBar).toHaveStyle({ width: '0%' });
  });

  it('handles 100% progress correctly', () => {
    render(<SimulationProgress {...defaultProps} progress={100} />);
    
    expect(screen.getByText('100%')).toBeInTheDocument();
    const progressBar = document.querySelector('.progress-fill');
    expect(progressBar).toHaveStyle({ width: '100%' });
  });

  it('rounds progress percentage to nearest whole number', () => {
    render(<SimulationProgress {...defaultProps} progress={33.7} />);
    
    expect(screen.getByText('34%')).toBeInTheDocument();
  });

  it('handles decimal elapsed time by flooring', () => {
    render(<SimulationProgress {...defaultProps} elapsedTime={45.8} />);
    
    expect(screen.getByText('Elapsed time: 45 seconds')).toBeInTheDocument();
  });

  it('handles decimal remaining time by ceiling', () => {
    render(<SimulationProgress {...defaultProps} estimatedRemaining={30.2} />);
    
    expect(screen.getByText('Estimated time remaining: 31 seconds')).toBeInTheDocument();
  });

  it('updates progress bar smoothly with transition class', () => {
    render(<SimulationProgress {...defaultProps} progress={60} />);
    
    const progressBar = document.querySelector('.progress-fill');
    expect(progressBar).toHaveClass('progress-fill');
  });

  it('step indicators show correct status based on progress', () => {
    render(<SimulationProgress {...defaultProps} progress={35} currentStep="Processing trading signals" />);
    
    // Check step indicator circles
    const stepIndicators = document.querySelectorAll('.w-4.h-4.rounded-full');
    
    // First step should be completed (green)
    expect(stepIndicators[0]).toHaveClass('bg-green-500');
    
    // Second step should be completed (green) 
    expect(stepIndicators[1]).toHaveClass('bg-green-500');
    
    // Third step should be current (blue, pulsing)
    expect(stepIndicators[2]).toHaveClass('bg-blue-600', 'animate-pulse');
    
    // Remaining steps should be pending (gray)
    expect(stepIndicators[3]).toHaveClass('bg-gray-300');
  });

  it('handles async onCancel function', async () => {
    const mockOnCancel = jest.fn().mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );
    const user = userEvent.setup();
    
    render(<SimulationProgress {...defaultProps} onCancel={mockOnCancel} />);
    
    const cancelButton = screen.getByRole('button', { name: /cancel simulation/i });
    await user.click(cancelButton);
    
    await waitFor(() => {
      expect(mockOnCancel).toHaveBeenCalledTimes(1);
    });
  });

  it('displays time information in correct section', () => {
    render(
      <SimulationProgress 
        {...defaultProps} 
        elapsedTime={60}
        estimatedRemaining={40}
        simulationId="test123"
      />
    );
    
    // All time-related info should be in the same section
    const timeSection = screen.getByText('Elapsed time: 60 seconds').closest('div');
    expect(timeSection).toContainElement(screen.getByText('Estimated time remaining: 40 seconds'));
    expect(timeSection).toContainElement(screen.getByText('Simulation ID: test123...'));
  });
});