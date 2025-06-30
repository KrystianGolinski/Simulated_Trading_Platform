# Simulated Trading Platform - Current Status Report

**Last Updated:** July 1, 2025  

## Version 1.1 

**Description:** 
Platform is correctly set up using 'setup.sh' featuring extensive and comprehensive testing ensuring:
- C++ engine is fully operational across all components
- API is fully operational and healthy across all endpoints
- Platform components are correctly interacting between each other

Platform is maintaining it's full docker containerisation, with containers sharing volumes and able to interact between each other.

The testing architecture is extensive, logging is setup for easy debugging, warnings displaying or generalised output. Errors are extensively created to determine causality easily. 

The user is correctly able to start a simulation from frontend with configurable parameters featuring multi-stock abilities (currently the platform has data for 25 symbols so that is the maximum but data limited not engine limited) and 2 strategies: MA_Crossover and RSI (Relative Strength Index). The strategies are successfully computed by the engine and the results are correctly displayed on the results screen. 

The platform now is starting to take shape, with clear future expansions planned.

**API**

The API is comprehensive, standardised and adequately documented at `Project_Documentation/APIstructure.md`

**Engine**

The engine succesfully powers the platform. Python FastAPI communicates with c++ engine via subprocess execution and JSON for data exchange. 

**Frontend**

The frontend is not the strong point of the platform just yet

**Data**

Daily data for 25 stocks for about 40 years, sufficient for testing. Needs scaling. Scaling infrastructure such as pagination is already in place, platform is scalable.

**Testing**

Extensive testing structure throughout, comprehensive debug options, easy error tracing for causation, very solid foundation to begin development. Testing coverage covers all crucial aspects of the platform ensuring integrity is maintained. Error handling is structured and categorised in the API.

**Multi-platformity**

Works on Linux. No Windows compatibility, not planned for anytime soon (bigger priorities).

**Scalability**

Platform is scalable, the current codebase is clean, maintainable and scalable (still a few improvements to go but already a strong foundation) providing the perfect start for expansions. Strategies use a plugin structure, with dynamic strategy parameter loading enabling new strategies to be added easily. Pagination with TimescaleDB PostgreSQL allows for future data expansions into new asset types and broader asset quantities. Engine utilises multi-threading with thread-safety prioritsied with mutex's ensuring more intensive simulations still get completed in swift manner. 

**Planned Improvements (Code Side)**

These improvements will generally not affect the overall usability of the platform to users or it's abilities but will improve code quality.

- Abstract base classes for engine services using interfaces
- Ensuring service configurations are centralized through dedicated service to implement configuration management
- Implement more `Project_Documentation/todo.md` to remove deadcode
- Remove code duplication where applicable
- Strenghten docker container healthchecks with endpoints
- Fix terrible frontend code
- Remove as many hardcoded code as possible and prioritise dynamic approaches

**Planned Major Expansions (User Side)**

These may be featured in version 2.0 of the platform. Improving code quality takes priority over these features.

- Multiple asset type simulations (Stocks, minerals, crypto etc)
- Fully customisable asset configurations in simulations
- Cleaner frontend (more graphs, better layout, less jank)
- More strategy types
- More data
- Simulation saving, exporting...
- General platform improvements