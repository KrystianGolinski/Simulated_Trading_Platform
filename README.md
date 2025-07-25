# Simulated Trading Platform - Current Status Report

**Last Updated:** July 9, 2025  

## Version 1.3 

## Description:

A full-stack containerised platform consisting of an **API** (built using FastAPI), **C++ Backend Engine** and **Frontend** (React). Perform simulations on **44** stocks for date ranges of up to **10 Years** using strategies such as **MA_Crossover** or **RSI (Relative Strength Index)** with custom parameters per strategy. View performance metrics and simulation results with graphs on frontend. 

## Install/Setup

The platform is designed to handle any Linux system. Internet access is required. The script 'setup.sh' uses sudo which is powerful and should be noted that any user running a command through sudo should verify the integrity of the ran files. The script requires it to install system-wide dependencies such as Docker or C++ libraries. After successful installation the platform can be used through localhost:3000/ and running simulations via the frontend.

- 1: Clone repository
- 2: Change directory to root `(Simulated_Trading_Platform)`
- 3: Execute `sudo bash setup.sh` to run setup script
- 4: If ran **Not Successfully**:
  - 4.1: The script should inform you what went wrong.
- 5: Once ran **Successfully**:
  - 6: Change directory to Database `(Simulated_Trading_Platform/Database)`
  - 7: Execute `sudo bash DBsetup.sh` to populate platform database
  - 8: If ran **Not Successfully**:
    - 8.1: The script should inform you what went wrong
  - 9: If ran **Successfully**:
      - 10: Frontend will be available at localhost:3000/
      - 11: API will be available at localhost:8000/
- 12: To end docker services use `sudo docker compose -f Docker/docker-compose.dev.yml down`
---

If you encounter any issues, the platform uses the following pre-requisites:

- **General**: Docker, cmake, libpq-dev, python3.12-venv (The rest **should** and have been tested to self-install)
- **For Database**: yfinance, pandas, psycopg2

Installing/checking the presence of these libraries **could** solve the errors you may encounter.

---
## Documentation

The documentation for each component of the projects can be found at:

- **API**: `Simulated_Trading_Platform/Project_Documentation/APIstructure.md`
- **Database**: `Simulated_Trading_Platform/Project_Documentation/DatabaseStructure.md`
- **Engine**: `Simulated_Trading_Platform/Project_Documentation/EngineStructure.md`

---

Legal Notice

Krystian Golinski 2025©

This project is for personal and showcase purposes only.

Unauthorized use, reproduction, distribution, or modification is not permitted without explicit written consent.

Do not copy or submit any part of this work as your own. All rights reserved.
