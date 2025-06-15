# Directory Structure

```
Simulated_Trading_Platform/
├── .git/
├── Backend/
│   ├── api/
│   │   ├── __pycache__/
│   │   ├── venv/
│   │   ├── .dockerignore
│   │   ├── Dockerfile
│   │   ├── main.py
        ├── database.py
│   │   ├── requirements.txt
│   │   └── setup_env.sh
│   ├── cpp-engine/
│   │   ├── include/
│   │   └── src/
│            ├── main.cpp
│   │   ├── CMakeLists.txt
│   │   └── Dockerfile
│   └── data-pipeline/
├── Database/
│   ├── historical_data/
│        ├── daily/
│            └── {STOCK}_daily.csv
│        ├── intraday/
│            └── {STOCK}_daily.csv
│        ├── stock_info.json
│        └── summary.json
│   ├── CSVtoPostgres.py
    ├── data_cleaning.py
    ├── data_integrity_verification.py
    ├── data_utils.py
    ├── DataGathering.py
    ├── test_connection.py
│   └── init.sql
├── Docker/
│   ├── docker-compose.dev.yaml
│   ├── docker-compose.yaml
│   └── docker-setup.sh
├── Frontend/
│   └── trading-platform-ui/
│       ├── node_modules/
│       ├── public/
│       ├── src/
│       ├── .dockerignore
│       ├── .gitignore
│       ├── Dockerfile
│       ├── package.json
│       ├── package-lock.json
│       └── tsconfig.json
├── Project_Documentation/
│   ├── Environment.md
│   ├── FileStructure.md
│   ├── Idea.md
│   ├── Knowledge.md
│   ├── Optimisations.md
│   └── Roadmap1.md
├── .env
├── .env.example
├── .gitignore
├── README.md
└── setup.sh
```