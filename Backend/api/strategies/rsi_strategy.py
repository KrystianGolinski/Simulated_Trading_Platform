# RSI (Relative Strength Index) Strategy Implementation
from typing import Dict, Any, List
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy_registry import StrategyInterface, StrategyMetadata, StrategyParameter

class RSIStrategy(StrategyInterface):
    # RSI strategy with dynamic parameter configuration for oversold/overbought conditions
    
    def get_metadata(self) -> StrategyMetadata:
        # Return comprehensive metadata for RSI strategy
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
        # Validate RSI strategy specific parameters
        errors = []
        
        rsi_oversold = parameters.get("rsi_oversold")
        rsi_overbought = parameters.get("rsi_overbought")
        
        if rsi_oversold and rsi_overbought:
            if rsi_oversold >= rsi_overbought:
                errors.append("RSI oversold threshold must be less than overbought threshold")
            
            # Check for reasonable gap between thresholds
            if rsi_overbought - rsi_oversold < 20:
                errors.append("RSI thresholds should have at least 20 point gap for meaningful signals")
        
        # Validate RSI period for stability
        rsi_period = parameters.get("rsi_period")
        if rsi_period and rsi_period < 10:
            errors.append("RSI period should be at least 10 for stable calculations")
        
        return errors
    
    def get_cpp_strategy_name(self) -> str:
        # Return C++ engine strategy identifier
        return "rsi"
    
    def transform_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Transform parameters for C++ engine compatibility
        return {
            "strategy": self.get_cpp_strategy_name(),
            "rsi_period": parameters.get("rsi_period", 14),
            "rsi_oversold": parameters.get("rsi_oversold", 30.0),
            "rsi_overbought": parameters.get("rsi_overbought", 70.0)
        }