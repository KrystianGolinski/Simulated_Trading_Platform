# Trade Converter - Trading Signal Processing and Trade Record Generation Service
# This module provides specialized conversion of trading signals into comprehensive trade records
#
# Architecture Overview:
# The TradeConverter implements sophisticated signal-to-trade conversion capabilities that transform
# raw trading signals from the C++ engine into structured trade records. It handles position
# management, profit/loss calculations, and trade lifecycle tracking for the trading platform.
#
# Key Responsibilities:
# 1. Trading signal validation and structure verification
# 2. Position management for buy/sell signal pairs
# 3. Profit/loss calculation for completed trades
# 4. Trade record generation with comprehensive metadata
# 5. Position sizing calculation based on available capital
# 6. Open position tracking and incomplete trade handling
#
# Signal Processing Pipeline:
# 1. Validate trading signals structure and content
# 2. Process buy signals to open new positions
# 3. Process sell signals to close positions and calculate P&L
# 4. Generate comprehensive trade records with profit/loss data
# 5. Handle incomplete trades for positions still open at end
# 6. Calculate position sizes based on capital allocation strategy
#
# Integration with Trading Platform:
# - Processes trading signals from C++ engine simulation output
# - Generates TradeRecord objects for API response consistency
# - Supports multiple position management strategies
# - Provides comprehensive trade validation and error handling
# - Integrates with portfolio and performance calculation systems
#
# Trade Record Features:
# - Complete buy/sell transaction pairs with profit/loss calculations
# - Position sizing based on configurable capital allocation
# - Trade date range tracking (entry to exit dates)
# - Percentage-based profit/loss reporting
# - Open position handling for incomplete trades
# - Comprehensive validation of signal data integrity

import logging
from datetime import datetime
from typing import Any, Dict, List

from models import TradeRecord

logger = logging.getLogger(__name__)


class TradeConverter:
    """
    Specialized service for converting trading signals into comprehensive trade records.

    This class provides sophisticated signal-to-trade conversion capabilities that transform
    raw trading signals from the C++ engine into structured trade records. It implements
    stateless operations for signal processing, position management, and profit/loss
    calculations to support the trading platform's analysis and reporting requirements.

    Key Features:
    - Stateless design for high-performance signal processing
    - Comprehensive position management for buy/sell signal pairs
    - Profit/loss calculation with percentage-based reporting
    - Position sizing based on configurable capital allocation strategies
    - Open position tracking for incomplete trades
    - Detailed trade validation and error handling

    The converter handles the complete lifecycle of trading positions, from signal
    generation through position opening, management, and closure with comprehensive
    profit/loss analysis.
    """

    def convert_signals_to_trades(
        self, signals_data: List[Dict[str, Any]], result_data: Dict[str, Any]
    ) -> List[TradeRecord]:
        """
        Convert trading signals into comprehensive trade records with profit/loss calculations.

        This method processes a sequence of trading signals to generate complete trade records
        that represent buy/sell transaction pairs. It manages position lifecycle, calculates
        profit/loss for completed trades, and handles open positions appropriately.

        Args:
            signals_data: List of trading signal dictionaries containing:
                - signal: "BUY" or "SELL" action type
                - price: Execution price for the signal
                - date: ISO-formatted date string for the signal
            result_data: Simulation result context containing symbol and capital information

        Returns:
            List[TradeRecord]: Comprehensive trade records containing:
                - Complete buy/sell pairs with profit/loss calculations
                - Open positions for incomplete trades
                - Position sizing and execution details
                - Date ranges and percentage-based returns

        Position Management:
        The method implements a simple position management strategy:
        1. BUY signals open new positions with calculated position sizing
        2. SELL signals close existing positions and calculate profit/loss
        3. Open positions at end are recorded as incomplete trades
        4. Position sizing is based on configurable capital allocation percentage

        The conversion provides comprehensive trade analysis suitable for performance
        evaluation and portfolio reporting.
        """
        trades = []
        open_positions = {}  # symbol -> {entry_signal, shares}
        symbol = result_data.get("symbol", "UNKNOWN")

        # Process each signal in chronological order
        for signal in signals_data:
            if not isinstance(signal, dict):
                continue

            signal_type = signal.get("signal", "").upper()
            price = signal.get("price", 0.0)
            date_str = signal.get("date", datetime.now().isoformat())

            if signal_type == "BUY":
                # Open a new position with calculated position sizing
                shares = self._calculate_position_size(price, result_data)
                open_positions[symbol] = {
                    "entry_date": date_str,
                    "entry_price": price,
                    "shares": shares,
                }

            elif signal_type == "SELL" and symbol in open_positions:
                # Close the position and create a comprehensive trade record
                position = open_positions[symbol]
                entry_price = position["entry_price"]
                shares = position["shares"]

                # Calculate comprehensive profit/loss metrics
                total_entry_value = entry_price * shares
                total_exit_value = price * shares
                profit_loss = total_exit_value - total_entry_value
                profit_loss_pct = (
                    (profit_loss / total_entry_value) * 100
                    if total_entry_value > 0
                    else 0.0
                )

                # Create comprehensive trade record for the completed trade
                trade = TradeRecord(
                    date=f"{position['entry_date']} -> {date_str}",  # Show complete date range
                    symbol=symbol,
                    action=f"BUY@{entry_price:.2f} -> SELL@{price:.2f} ({profit_loss_pct:+.2f}%)",
                    shares=shares,
                    price=entry_price,  # Entry price for reference
                    total_value=profit_loss,  # Net profit/loss as total value
                )
                trades.append(trade)

                # Remove the closed position from tracking
                del open_positions[symbol]

        # Handle any remaining open positions as incomplete trades
        for symbol, position in open_positions.items():
            trade = TradeRecord(
                date=f"{position['entry_date']} (OPEN)",
                symbol=symbol,
                action=f"BUY@{position['entry_price']:.2f} (POSITION OPEN)",
                shares=position["shares"],
                price=position["entry_price"],
                total_value=0.0,  # No profit/loss for open positions
            )
            trades.append(trade)

        return trades

    def _calculate_position_size(
        self, price: float, result_data: Dict[str, Any]
    ) -> int:
        """
        Calculate position size based on available capital and allocation strategy.

        This method implements a position sizing strategy that allocates a fixed
        percentage of total capital to each trade. It ensures reasonable position
        sizes while maintaining proper risk management principles.

        Args:
            price: Current stock price for position sizing calculation
            result_data: Simulation context containing capital information

        Returns:
            int: Number of shares to purchase (minimum 1 share)

        Position Sizing Strategy:
        - Uses fixed percentage of total capital per trade (default 10%)
        - Calculates maximum shares affordable at current price
        - Ensures minimum position size of 1 share
        - Could be enhanced with dynamic position sizing based on volatility
        """
        starting_capital = result_data.get("starting_capital", 10000.0)

        # Simple strategy: use a fixed percentage of capital per trade
        POSITION_SIZE_PCT = (
            0.1  # Default position size percentage - could be made configurable
        )
        position_size_pct = POSITION_SIZE_PCT
        available_capital = starting_capital * position_size_pct

        if price > 0:
            shares = int(available_capital / price)
            return max(1, shares)  # At least 1 share
        return 1

    def validate_signals(self, signals: Any) -> bool:
        """
        Comprehensive validation of trading signals structure and content.

        This method performs thorough validation of trading signal data to ensure
        data integrity, proper formatting, and compliance with trading requirements.
        It validates both the overall structure and individual signal components.

        Args:
            signals: Trading signals data to validate (should be list of dictionaries)

        Returns:
            bool: True if signals data is valid, False otherwise

        Validation Criteria:
        - Must be a list structure
        - Each signal must be a dictionary
        - Each signal must contain required fields: 'signal', 'price', 'date'
        - Signal types must be 'BUY' or 'SELL'
        - Prices must be positive numbers (int or float)
        - Dates must be string format with minimum length

        The method provides detailed error logging for each validation failure,
        enabling precise debugging and data quality monitoring.
        """
        if not isinstance(signals, list):
            logger.error("signals must be a list")
            return False

        # Validate each trading signal
        for i, signal in enumerate(signals):
            if not isinstance(signal, dict):
                logger.error(f"Signal {i} must be a dictionary")
                return False

            # Validate required signal fields presence
            required_signal_fields = ["signal", "price", "date"]
            for field in required_signal_fields:
                if field not in signal:
                    logger.error(f"Signal {i} missing required field: {field}")
                    return False

            # Validate signal type constraints
            signal_type = signal.get("signal", "").upper()
            if signal_type not in ["BUY", "SELL"]:
                logger.error(f"Signal {i} has invalid signal type: {signal_type}")
                return False

            # Validate price field constraints
            price = signal.get("price")
            if not isinstance(price, (int, float)) or price <= 0:
                logger.error(f"Signal {i} has invalid price: {price}")
                return False

            # Validate date field format (basic check)
            date_str = signal.get("date")
            if not isinstance(date_str, str) or len(date_str) < 8:
                logger.error(f"Signal {i} has invalid date format: {date_str}")
                return False

        return True
