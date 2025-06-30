import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class EquityProcessor:
    # No initialization needed for stateless processing operations
    
    def process_equity_curve(self, result_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Process equity curve data from C++ engine output
        return result_data.get("equity_curve", [])
    
    def validate_equity_curve(self, equity_curve: Any) -> bool:
        # Validate equity_curve array structure and content
        if not isinstance(equity_curve, list):
            logger.error("equity_curve must be a list")
            return False
        
        for i, point in enumerate(equity_curve):
            if not isinstance(point, dict):
                logger.error(f"Equity curve point {i} must be a dictionary")
                return False
            
            # Required equity curve fields
            required_fields = ["date", "value"]
            for field in required_fields:
                if field not in point:
                    logger.error(f"Equity curve point {i} missing required field: {field}")
                    return False
            
            # Validate values
            value = point.get("value")
            if not isinstance(value, (int, float)) or value < 0:
                logger.error(f"Equity curve point {i} has invalid value: {value}")
                return False
            
            date_str = point.get("date")
            if not isinstance(date_str, str):
                logger.error(f"Equity curve point {i} has invalid date format: {date_str}")
                return False
        
        return True