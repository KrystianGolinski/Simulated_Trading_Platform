# Simulated Stock Trading Platform

**Current State of the Project:**

Currently the software collects historical (10 year) data from stocks:

AAPL, MSFT, GOOGL, AMZN, META,TSLA, NVDA, JPM, V, JNJ, WMT, PG, UNH, HD, DIS, MA, BAC, ADBE, CRM, NFLX, X, T, QCOM, ^SPX, ^NYA

at intraday and daily intervals. The acquired data (Yahoo Finance API) is cleaned to ensure completeness, authenticity and accuracy and then validated using tests to minimise erroneous results.

The current project has barebone environments set up to work with C++ (CMake), FastAPI and PostgreSQL (timescaleDB). These are set up within a container using Docker to allow multi-platform transferability of project. Currently tested to work on Windows and Linux. The project works on multiple platforms.

**Goal of the Project:**

The goal is to have a web-based platform which the user can enter parameters for simulators to showcase stock market trading results and strategies. A sample simulation might be:

Simulate ROI on £1,000 over 6 years using simple moving average strategy.

The simulation should run swfitly, with the ability to slow down for the user when indicated, and make optimal calls and strategic decisions to hopefully increase the starting capital. At the end the platform would display the final amount of capital, amount of trades, volume traded alongside other KPIs. Each trade should be shown (if slowed down enough) providing an educational aspect and showcasing the power of investing. Some strategies might be riskier than others which will also be outlined to the user. 