# Test Data Documentation

Standardized test data for the Simulated Trading Platform integration tests.

## Directory Structure

```
test_data/
├── sample_configs/                  # Sample simulation configurations
│   ├── basic_ma_crossover.json      # Basic single-stock MA crossover
│   ├── multi_stock_portfolio.json   # Multi-stock portfolio test
│   ├── rsi_strategy.json            # RSI strategy configuration  
│   └── invalid_configs.json         # Invalid configurations for error testing
├── mock_responses/                  # Mock API responses for testing
│   ├── simulation_responses.json    # Simulation API mock responses
│   └── api_responses.json           # General API mock responses
├── datasets/                        # Sample datasets (accounts future expansion)
└── README.md                        # This documentation
```

## Usage

### Sample Configurations

Use the JSON files to test different simulation scenarios:

- **basic_ma_crossover.json**: Simple single-stock test for basic functionality
- **multi_stock_portfolio.json**: Complex multi-stock test for comprehensive scenarios
- **rsi_strategy.json**: RSI strategy testing (when implemented)
- **invalid_configs.json**: Collection of invalid configurations for error handling tests

### Mock Responses

The mock responses are used by:
- Frontend unit tests (MSW handlers)
- Integration test scripts
- API endpoint testing

### Integration with Test Scripts

The enhanced integration test scripts automatically:
1. Check for test data consistency
2. Use sample configurations for validation testing
3. Compare actual API responses with expected mock responses
4. Validate data format consistency

## Integration Testing

This test data supports:
- Consistent sample datasets for reproducible testing
- Database failure scenario testing data
- Comprehensive error scenario test cases
- Test data isolation and management
