"""
RSI (Relative Strength Index) Strategy Implementation

This module implements a momentum-based trading strategy using the Relative Strength Index (RSI),
a popular oscillator that measures the speed and magnitude of price changes. The strategy
identifies overbought and oversold conditions to generate contrarian trading signals.

Strategy Logic:
- BUY Signal: When RSI falls below oversold threshold (typically 30)
- SELL Signal: When RSI rises above overbought threshold (typically 70)

Technical Analysis Foundation:
RSI is a momentum oscillator that ranges from 0 to 100, developed by J. Welles Wilder.
It compares the magnitude of recent gains to recent losses to determine overbought
and oversold conditions. The strategy assumes that extreme RSI values indicate
potential price reversals.

Strategy Parameters:
- rsi_period: Number of periods for RSI calculation (default: 14)
- rsi_oversold: RSI threshold for oversold condition (default: 30.0)
- rsi_overbought: RSI threshold for overbought condition (default: 70.0)

Risk Profile:
- Risk Level: Medium
- Strategy Type: Mean Reversion/Momentum
- Oscillator-based: Yes
- False Signals: Can generate whipsaws in strong trending markets

Integration with Platform:
- Implements StrategyInterface for consistent API interaction
- Provides metadata for strategy registry discovery
- Validates parameters for logical threshold relationships
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

class RSIStrategy(StrategyInterface):
    """
    RSI (Relative Strength Index) Strategy Implementation
    
    This class implements a momentum-based trading strategy using RSI oscillator values
    to identify overbought and oversold market conditions. It inherits from StrategyInterface
    to ensure consistent integration with the platform's strategy system.
    
    Key Features:
    - Configurable RSI calculation period
    - Adjustable overbought/oversold thresholds
    - Parameter validation for logical threshold relationships
    - Integration with C++ simulation engine
    - Metadata provision for strategy discovery and UI display
    
    Signal Generation:
    - Long Entry: RSI falls below oversold threshold (mean reversion)
    - Long Exit: RSI rises above overbought threshold (profit taking)
    - Strategy assumes long-only positions (no short selling)
    
    Performance Characteristics:
    - Works best in range-bound/sideways markets
    - May generate false signals in strong trending markets
    - Requires sufficient historical data for RSI calculation stability
    
    Thread Safety:
    - This class is stateless and thread-safe
    - Can be used in parallel simulation execution
    """
    
    def get_metadata(self) -> StrategyMetadata:
        """
        Provides comprehensive metadata for the RSI strategy.
        
        This metadata is used by the strategy registry for discovery, the API for
        endpoint responses, and the frontend for user interface display.
        
        Returns:
            StrategyMetadata: Complete strategy metadata including:
                - Strategy identification and display information
                - Required technical indicators (RSI)
                - Parameter definitions with validation rules
                - Risk level and category classification
                - Minimum data requirements for execution
        
        Strategy Classification:
            - Category: momentum
            - Risk Level: medium
            - Required Indicators: Relative Strength Index (RSI)
            - Min Data Points: 100 (ensures stable RSI calculation)
        """
        return StrategyMetadata(
            strategy_id="rsi",
            display_name="RSI Momentum Strategy",
            description="Uses Relative Strength Index to identify oversold and overbought conditions. "
                       "Buy signals when RSI falls below oversold threshold, sell when RSI rises above overbought threshold.",
            version="1.0.0", 
            author="Trading Platform Core",
            category="momentum",
            risk_level="medium",
            requires_indicators=["RSI"],
            min_data_points=100,  # Need enough data for RSI calculation stability
            parameters=[
                StrategyParameter(
                    name="rsi_period",
                    param_type=int,
                    default=14,
                    min_value=5,
                    max_value=50,
                    description="Period for RSI calculation",
                    required=True
                ),
                StrategyParameter(
                    name="rsi_oversold",
                    param_type=float,
                    default=30.0,
                    min_value=10.0,
                    max_value=40.0,
                    description="RSI threshold for oversold condition (buy signal)",
                    required=True
                ),
                StrategyParameter(
                    name="rsi_overbought",
                    param_type=float,
                    default=70.0,
                    min_value=60.0,
                    max_value=90.0,
                    description="RSI threshold for overbought condition (sell signal)",
                    required=True
                )
            ]
        )
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """
        Validates RSI strategy parameters for logical consistency and technical soundness.
        
        This method performs business logic validation beyond basic type checking.
        It ensures that RSI thresholds create meaningful overbought/oversold signals
        and follow technical analysis best practices.
        
        Args:
            parameters (Dict[str, Any]): Strategy parameters to validate
                - rsi_period: RSI calculation period
                - rsi_oversold: Oversold threshold for buy signals
                - rsi_overbought: Overbought threshold for sell signals
        
        Returns:
            List[str]: List of validation error messages. Empty list if valid.
        
        Validation Rules:
            1. rsi_oversold must be less than rsi_overbought
            2. Thresholds should have at least 20 point gap for meaningful signals
            3. RSI period should be at least 10 for stable calculations
        
        Business Logic:
            - Prevents invalid threshold configurations
            - Ensures sufficient signal separation for clear trading decisions
            - Follows technical analysis best practices for RSI parameters
        """
        errors = []
        
        rsi_oversold = parameters.get("rsi_oversold")
        rsi_overbought = parameters.get("rsi_overbought")
        
        # Validate RSI threshold relationship for proper signal generation
        if rsi_oversold and rsi_overbought:
            if rsi_oversold >= rsi_overbought:
                errors.append("RSI oversold threshold must be less than overbought threshold")
            
            # Ensure sufficient gap between thresholds for meaningful signals
            # Technical analysis best practice: adequate separation prevents whipsaws
            if rsi_overbought - rsi_oversold < 20:
                errors.append("RSI thresholds should have at least 20 point gap for meaningful signals")
        
        # Validate RSI period for calculation stability
        # Shorter periods create more volatile RSI values
        rsi_period = parameters.get("rsi_period")
        if rsi_period and rsi_period < 10:
            errors.append("RSI period should be at least 10 for stable calculations")
        
        return errors
    
    def get_cpp_strategy_name(self) -> str:
        """
        Returns the C++ engine strategy identifier for this RSI strategy.
        
        This identifier must match the strategy name registered in the C++ simulation
        engine. The engine uses this name to route strategy parameters to the correct
        RSI implementation for signal generation and backtesting.
        
        Returns:
            str: C++ engine strategy identifier "rsi"
        
        Integration Notes:
            - Must match C++ engine strategy registry
            - Used by simulation_engine.py for strategy execution
            - Enables seamless Python-to-C++ strategy communication
        """
        return "rsi"
    
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
                - rsi_period: RSI calculation period (int)
                - rsi_oversold: Oversold threshold (float)
                - rsi_overbought: Overbought threshold (float)
        
        Transformation Details:
            - Adds strategy identifier for C++ engine routing
            - Applies default values for missing parameters
            - Ensures parameter names match C++ engine expectations
            - Maintains type consistency between Python and C++ interfaces
        """
        return {
            "strategy": self.get_cpp_strategy_name(),         # C++ engine strategy identifier
            "rsi_period": parameters.get("rsi_period", 14),     # Default: 14-period RSI
            "rsi_oversold": parameters.get("rsi_oversold", 30.0),   # Default: 30 oversold level
            "rsi_overbought": parameters.get("rsi_overbought", 70.0) # Default: 70 overbought level
        }