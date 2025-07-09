# TODO: These Python strategies will not be as performant as C++ engine strategies
# Example Plugin Strategy: Bollinger Bands Strategy
import os
import sys
from typing import Any, Dict, List

# Add parent directories to path for imports
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from strategy_registry import StrategyInterface, StrategyMetadata, StrategyParameter


class BollingerBandsStrategy(StrategyInterface):
    # Bollinger Bands strategy - example of adding new strategy via plugin system

    def get_metadata(self) -> StrategyMetadata:
        # Return metadata for Bollinger Bands strategy
        return StrategyMetadata(
            strategy_id="bollinger_bands",
            display_name="Bollinger Bands Strategy",
            description="Uses Bollinger Bands to identify overbought/oversold conditions. "
            "Buy signals when price touches lower band, sell when price touches upper band.",
            version="1.0.0",
            author="Plugin Developer",
            category="volatility",
            risk_level="high",
            requires_indicators=["SMA", "BollingerBands"],
            min_data_points=40,  # Need enough data for moving average + volatility
            parameters=[
                StrategyParameter(
                    name="bb_period",
                    param_type=int,
                    default=20,
                    min_value=10,
                    max_value=50,
                    description="Period for Bollinger Bands calculation",
                    required=True,
                ),
                StrategyParameter(
                    name="bb_deviation",
                    param_type=float,
                    default=2.0,
                    min_value=1.0,
                    max_value=3.0,
                    description="Standard deviation multiplier for bands",
                    required=True,
                ),
                StrategyParameter(
                    name="bb_oversold_pct",
                    param_type=float,
                    default=5.0,
                    min_value=1.0,
                    max_value=20.0,
                    description="Percentage below lower band to trigger buy signal",
                    required=False,
                ),
            ],
        )

    def validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        # Validate Bollinger Bands specific parameters
        errors = []

        bb_period = parameters.get("bb_period")
        bb_deviation = parameters.get("bb_deviation")
        bb_oversold_pct = parameters.get("bb_oversold_pct")

        # Validate period for stability
        if bb_period and bb_period < 15:
            errors.append(
                "Bollinger Bands period should be at least 15 for stable calculations"
            )

        # Validate deviation range
        if bb_deviation and (bb_deviation < 1.5 or bb_deviation > 2.5):
            errors.append(
                "Bollinger Bands deviation should be between 1.5 and 2.5 for meaningful signals"
            )

        # Validate oversold percentage
        if bb_oversold_pct and bb_oversold_pct > 10.0:
            errors.append(
                "Oversold percentage should not exceed 10% for practical trading"
            )

        return errors

    def get_cpp_strategy_name(self) -> str:
        # Return C++ engine strategy identifier (would need C++ implementation)
        return "bollinger_bands"

    def transform_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Transform parameters for C++ engine compatibility
        return {
            "strategy": self.get_cpp_strategy_name(),
            "bb_period": parameters.get("bb_period", 20),
            "bb_deviation": parameters.get("bb_deviation", 2.0),
            "bb_oversold_pct": parameters.get("bb_oversold_pct", 5.0),
        }
