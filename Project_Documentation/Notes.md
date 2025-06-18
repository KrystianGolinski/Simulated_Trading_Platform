### Notes:

**Redis**

Current approach does not cache using Redis, consider removal or migration. Docker container for Redis has been removed, scrub Redis information from codebase and information

**Simulation.py**

Code repetition - When starting a simulation it performs validity checks exactly to '/simulation/validate'

HTPP Code - When returning validation errors the HTTP code is 400 not 500

Simulation cancelling endpoint - Would we ever need to cancel a simulation? (Possible bloat?)

**Stocks.py**

Data retrieval - When retrieving stock data is only daily data considered? Missing intraday?

**Database.py**

Missing error output - '_get_cache' returns if key not valid with no further output

Adjust error tolerance / gaps - 'validate_date_range_has_data' requires only 50% of data, with new data acquisition this should increment

Implementation - is 'validate_multiple_symbols' implemented yet? Running simulation through the frontend port 3000 only accounts for one symbol.

**models.py**

RSI - Is RSI implemented yet (included in strategy-specific parameters)?

**performance_optimizer.py**

TODO: optimize_multi_symbol_simulation and execute_parallel_simulation_groups (Line 64 and 85)

**simulation_engine.py**

Possible bloat - PerformanceOptimizer is not accessed/used?

Docker - Always assume we are in docker, reduce code

Code repetition - 2 methods to validate cpp engine?

Line 146 - Implement multi-symbol simulation

Line 159+ - RSI is not implemented?

Line 194 - Not that useful at the moment (Singular symbol support and singular strategy support)

Line 220 - This way used to fix a bug with incorrect directory creation, is it still needed and can it be optimised?

Line 386 - Are suggestions necessary?

Line 513 - Estimation is not going to be accurate, very variable. Consider removal

Line 529 - Would we ever need to cancel a simulation? (Possible bloat?) (Line 11 of this file)

**test_startup.py**

Necessity - Is it necessary? Can it be integrated with the comprehensive test file to avoid bloat? It is never called or used externally

**validation.py**

Imports - datetime and timedelta seem obsolete from datetime

Early exit - validate_simulation_config checks all parameters even if symbol is incorrect, possible inefficiency. Maybe implement an early exit strategy with hindered error returns?

Line 94 - Why suggests stock if it's a checkbox from a pre-defined list?

Line 177 - As strategies get developed with multi-symbolic execution consider lowering this amount

Line 214 - RSI is not implemented?

Line 251 - When optimised, at full release, will become obsolete as simulations of 10/15 years will be the norm

Line 281 - Why are we using suggested stocks, what is the purpose of this code?

**Backend/cpp-engine/tests**

Tests - Comprehensive shell tests and basic cpp testing, merge into one test file to cover all?

**Database/test_connection.py**

Unnecessary config paths, use default: localhost, simulated_trading_platform, trading_user, trading_password

**Database/CSVtoPostgres.py**

Do we need to set a refresh policy if we only use historical data? (Line 330, 408, 409 etc ...)

**Database/data_cleaning.py**

data_cleaning.py and data_integrity_verification.py have overlapping checks, merge and adjust accordingly

**Database/data_utils.py**

In future, ensure consistent DB formatiing between daily and intraday to remove get_date_column and reduce the necessity of this file

**Database/DataGathering.py**

Always save to csv then import to DB with CSVtoPostgres, remove argument and functionality to import straight to DB within the file

**Docker/docker-compose.yml**

Remove Redis as not used currently and docker-compose.dev.yml has it removed

**Backend/cpp-engine/trading_engine**

Legacy simulation method and parameterised method, merge or remove legacy. Seems like there are multiple obsolete functions

Line 389 - Allow to increase existing position in the future

**Backend/cpp-engine/trading_strategy**

Line 97 - Allow to increase existing position in the future (Line 109 of this file)

**Backend/cpp-engine/technical_indicators.cpp**

Multiple functions check for 'Period' to be positive (code repetition)

**Backend/cpp-engine/portfolio.cpp**

Usage/necessity of toDetailedString?

**Backend/cpp-engine/database_connection.cpp**

Lines 283 onwards: always ran within docker with known credentials, possibly reduction/merging to reduce code?


**TODO:**

/Backend/cpp-engine/*