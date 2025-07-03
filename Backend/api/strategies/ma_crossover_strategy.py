# Moving Average Crossover Strategy Implementation
from typing import Dict, Any, List
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy_registry import StrategyInterface, StrategyMetadata, StrategyParameter

class MACrossoverStrategy(StrategyInterface):
    # Moving Average Crossover strategy with dynamic parameter configuration
    
    def get_metadata(self) -> StrategyMetadata:
        # Return metadata for MA Crossover strategy
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
        # Validate MA crossover specific parameters
        errors = []
        
        short_ma = parameters.get("short_ma")
        long_ma = parameters.get("long_ma")
        
        if short_ma and long_ma:
            if short_ma >= long_ma:
                errors.append("Short MA period must be less than long MA period")
            
            # Check for reasonable ratios
            if long_ma / short_ma < 1.5:
                errors.append("Long MA should be at least 1.5x the short MA for meaningful crossovers")
        
        return errors
    
    def get_cpp_strategy_name(self) -> str:
        # Return C++ engine strategy identifier
        return "ma_crossover"
    
    def transform_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Transform parameters for C++ engine compatibility
        return {
            "strategy": self.get_cpp_strategy_name(),
            "short_ma": parameters.get("short_ma", 20),
            "long_ma": parameters.get("long_ma", 50)
        }