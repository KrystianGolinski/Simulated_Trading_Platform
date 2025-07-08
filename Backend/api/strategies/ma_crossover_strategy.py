"""
Moving Average Crossover Strategy Implementation

This module implements a classic technical analysis strategy based on moving average crossovers.
The strategy generates buy/sell signals when short-term and long-term moving averages intersect,
indicating potential trend changes in stock prices.

Strategy Logic:
- BUY Signal: When short-term MA crosses above long-term MA (bullish crossover)
- SELL Signal: When short-term MA crosses below long-term MA (bearish crossover)

Technical Analysis Foundation:
Moving average crossovers are one of the most widely used trend-following indicators.
The strategy assumes that when a shorter-period moving average crosses above a longer-period
moving average, it indicates upward momentum that will continue. Conversely, when the short
MA crosses below the long MA, it signals potential downward momentum.

Strategy Parameters:
- short_ma: Period for short-term moving average (default: 20 days)
- long_ma: Period for long-term moving average (default: 50 days)

Risk Profile:
- Risk Level: Medium
- Trend Following: Yes
- Lagging Indicator: Yes (moving averages are inherently lagging)
- False Signals: Can generate whipsaws in sideways markets

Integration with Platform:
- Implements StrategyInterface for consistent API interaction
- Provides metadata for strategy registry discovery
- Validates parameters for logical consistency
- Transforms parameters for C++ engine compatibility

Related Files:
- strategy_registry.py: Registers this strategy for discovery
- strategy_factory.py: Instantiates strategy with user parameters
- simulation_engine.py: Executes strategy via C++ engine
"""

from typing import Dict, Any, List
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy_registry import StrategyInterface, StrategyMetadata, StrategyParameter

class MACrossoverStrategy(StrategyInterface):
    """
    Moving Average Crossover Strategy Implementation
    
    This class implements a trend-following strategy that uses the crossover of two moving
    averages to generate trading signals. It inherits from StrategyInterface to ensure
    consistent integration with the platform's strategy system.
    
    Key Features:
    - Configurable short and long moving average periods
    - Parameter validation to ensure logical MA relationships
    - Integration with C++ simulation engine
    - Metadata provision for strategy discovery and UI display
    
    Signal Generation:
    - Long Entry: Short MA crosses above Long MA
    - Long Exit: Short MA crosses below Long MA
    - Strategy assumes long-only positions (no short selling)
    
    Performance Characteristics:
    - Works best in trending markets
    - May generate false signals in choppy/sideways markets
    - Requires sufficient historical data for MA calculation
    
    Thread Safety:
    - This class is stateless and thread-safe
    - Can be used in parallel simulation execution
    """
    
    def get_metadata(self) -> StrategyMetadata:
        """
        Provides comprehensive metadata for the Moving Average Crossover strategy.
        
        This metadata is used by the strategy registry for discovery, the API for
        endpoint responses, and the frontend for user interface display.
        
        Returns:
            StrategyMetadata: Complete strategy metadata including:
                - Strategy identification and display information
                - Required technical indicators (SMA)
                - Parameter definitions with validation rules
                - Risk level and category classification
                - Minimum data requirements for execution
        
        Strategy Classification:
            - Category: trend_following
            - Risk Level: medium
            - Required Indicators: Simple Moving Average (SMA)
            - Min Data Points: 200 (ensures stable long MA calculation)
        """
        return StrategyMetadata(
            strategy_id="ma_crossover",
            display_name="Moving Average Crossover",
            description="Generates buy/sell signals based on short-term and long-term moving average crossovers. "
                       "Buy when short MA crosses above long MA, sell when short MA crosses below long MA.",
            version="1.0.0",
            author="Trading Platform Core",
            category="trend_following",
            risk_level="medium",
            requires_indicators=["SMA"],
            min_data_points=200,  # Need enough data for long MA calculation
            parameters=[
                StrategyParameter(
                    name="short_ma",
                    param_type=int,
                    default=20,
                    min_value=5,
                    max_value=100,
                    description="Period for short-term moving average",
                    required=True
                ),
                StrategyParameter(
                    name="long_ma", 
                    param_type=int,
                    default=50,
                    min_value=10,
                    max_value=200,
                    description="Period for long-term moving average",
                    required=True
                )
            ]
        )
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """
        Validates Moving Average Crossover strategy parameters for logical consistency.
        
        This method performs business logic validation beyond basic type checking.
        It ensures that the MA periods create meaningful crossover signals and
        follow technical analysis best practices.
        
        Args:
            parameters (Dict[str, Any]): Strategy parameters to validate
                - short_ma: Short-term moving average period
                - long_ma: Long-term moving average period
        
        Returns:
            List[str]: List of validation error messages. Empty list if valid.
        
        Validation Rules:
            1. short_ma must be less than long_ma (fundamental crossover requirement)
            2. long_ma should be at least 1.5x short_ma for meaningful signals
            3. Parameters should create sufficient signal separation
        
        Business Logic:
            - Prevents invalid configurations that would never generate signals
            - Ensures sufficient separation between MAs for clear crossover detection
            - Follows technical analysis best practices for MA ratios
        """
        errors = []
        
        short_ma = parameters.get("short_ma")
        long_ma = parameters.get("long_ma")
        
        # Validate MA period relationship for proper crossover functionality
        if short_ma and long_ma:
            if short_ma >= long_ma:
                errors.append("Short MA period must be less than long MA period")
            
            # Ensure sufficient ratio for meaningful crossover signals
            # Technical analysis best practice: long MA should be significantly longer
            if long_ma / short_ma < 1.5:
                errors.append("Long MA should be at least 1.5x the short MA for meaningful crossovers")
        
        return errors
    
    def get_cpp_strategy_name(self) -> str:
        """
        Returns the C++ engine strategy identifier for this strategy.
        
        This identifier must match the strategy name registered in the C++ simulation
        engine. The engine uses this name to route strategy parameters to the correct
        implementation for signal generation and backtesting.
        
        Returns:
            str: C++ engine strategy identifier "ma_crossover"
        
        Integration Notes:
            - Must match C++ engine strategy registry
            - Used by simulation_engine.py for strategy execution
            - Enables seamless Python-to-C++ strategy communication
        """
        return "ma_crossover"
    
    def transform_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transforms Python strategy parameters for C++ engine compatibility.
        
        This method converts the Python parameter dictionary into the format expected
        by the C++ simulation engine. It ensures proper parameter naming, type conversion,
        and provides default values for missing parameters.
        
        Args:
            parameters (Dict[str, Any]): Raw strategy parameters from API request
        
        Returns:
            Dict[str, Any]: Transformed parameters for C++ engine including:
                - strategy: C++ strategy identifier
                - short_ma: Short moving average period (int)
                - long_ma: Long moving average period (int)
        
        Transformation Details:
            - Adds strategy identifier for C++ engine routing
            - Applies default values for missing parameters
            - Ensures parameter names match C++ engine expectations
            - Maintains type consistency between Python and C++ interfaces
        """
        return {
            "strategy": self.get_cpp_strategy_name(),  # C++ engine strategy identifier
            "short_ma": parameters.get("short_ma", 20),  # Default: 20-day short MA
            "long_ma": parameters.get("long_ma", 50)     # Default: 50-day long MA
        }