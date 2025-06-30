import logging
from datetime import datetime
from typing import Dict, Any, List
from models import TradeRecord

logger = logging.getLogger(__name__)

class TradeConverter:
    # No initialization needed for stateless conversion operations
    
    def convert_signals_to_trades(self, signals_data: List[Dict[str, Any]], result_data: Dict[str, Any]) -> List[TradeRecord]:
        # Convert trading signals into proper trade pairs with profit/loss calculations
        trades = []
        open_positions = {}  # symbol -> {entry_signal, shares}
        symbol = result_data.get("symbol", "UNKNOWN")
        
        for signal in signals_data:
            if not isinstance(signal, dict):
                continue
                
            signal_type = signal.get("signal", "").upper()
            price = signal.get("price", 0.0)
            date_str = signal.get("date", datetime.now().isoformat())
            
            if signal_type == "BUY":
                # Open a new position
                shares = self._calculate_position_size(price, result_data)
                open_positions[symbol] = {
                    "entry_date": date_str,
                    "entry_price": price,
                    "shares": shares
                }
                
            elif signal_type == "SELL" and symbol in open_positions:
                # Close the position and create a trade record
                position = open_positions[symbol]
                entry_price = position["entry_price"]
                shares = position["shares"]
                
                # Calculate profit/loss
                total_entry_value = entry_price * shares
                total_exit_value = price * shares
                profit_loss = total_exit_value - total_entry_value
                profit_loss_pct = (profit_loss / total_entry_value) * 100 if total_entry_value > 0 else 0.0
                
                # Create trade record for the completed trade
                trade = TradeRecord(
                    date=f"{position['entry_date']} -> {date_str}",  # Show entry and exit dates
                    symbol=symbol,
                    action=f"BUY@{entry_price:.2f} -> SELL@{price:.2f} ({profit_loss_pct:+.2f}%)",
                    shares=shares,
                    price=entry_price,  # Entry price
                    total_value=profit_loss  # Profit/loss as total value
                )
                trades.append(trade)
                
                # Remove the closed position
                del open_positions[symbol]
        
        # Handle any remaining open positions as incomplete trades
        for symbol, position in open_positions.items():
            trade = TradeRecord(
                date=f"{position['entry_date']} (OPEN)",
                symbol=symbol,
                action=f"BUY@{position['entry_price']:.2f} (POSITION OPEN)",
                shares=position["shares"],
                price=position["entry_price"],
                total_value=0.0  # No profit/loss for open positions
            )
            trades.append(trade)
        
        return trades
    
    def _calculate_position_size(self, price: float, result_data: Dict[str, Any]) -> int:
        # Calculate how many shares to buy based on available capital and strategy
        starting_capital = result_data.get("starting_capital", 10000.0)
        
        # Simple strategy: use a fixed percentage of capital per trade
        POSITION_SIZE_PCT = 0.1  # Default position size percentage - could be made configurable
        position_size_pct = POSITION_SIZE_PCT
        available_capital = starting_capital * position_size_pct
        
        if price > 0:
            shares = int(available_capital / price)
            return max(1, shares)  # At least 1 share
        return 1
    
    def validate_signals(self, signals: Any) -> bool:
        # Validate signals array structure and content
        if not isinstance(signals, list):
            logger.error("signals must be a list")
            return False
        
        for i, signal in enumerate(signals):
            if not isinstance(signal, dict):
                logger.error(f"Signal {i} must be a dictionary")
                return False
            
            # Required signal fields
            required_signal_fields = ["signal", "price", "date"]
            for field in required_signal_fields:
                if field not in signal:
                    logger.error(f"Signal {i} missing required field: {field}")
                    return False
            
            # Validate signal values
            signal_type = signal.get("signal", "").upper()
            if signal_type not in ["BUY", "SELL"]:
                logger.error(f"Signal {i} has invalid signal type: {signal_type}")
                return False
            
            price = signal.get("price")
            if not isinstance(price, (int, float)) or price <= 0:
                logger.error(f"Signal {i} has invalid price: {price}")
                return False
            
            # Validate date format (basic check)
            date_str = signal.get("date")
            if not isinstance(date_str, str) or len(date_str) < 8:
                logger.error(f"Signal {i} has invalid date format: {date_str}")
                return False
        
        return True