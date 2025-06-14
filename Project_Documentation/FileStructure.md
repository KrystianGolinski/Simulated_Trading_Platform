# Directory Structure

```
Simulated_Trading_Platform/
├── .git/
├── .github/
│   └── workflows/
├── Backend/
│   ├── api/
│   │   ├── __pycache__/
│   │   ├── venv/
│   │   ├── .dockerignore
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── README.md
│   │   ├── requirements.txt
│   │   └── setup_env.sh
│   ├── cpp-engine/
│   │   ├── build/
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
│   └── DataGathering.py
├── Docker/
│   ├── .env.example
│   ├── docker-compose.dev.yaml
│   ├── docker-compose.yaml
│   ├── docker-setup.sh
│   └── README.md
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
│       ├── README.md
│       └── tsconfig.json
├── Project_Documentation/
│   ├── Diagrams/
│   │   ├── DataFlowDiagram.png
│   │   ├── ErrorHandlingAndRecoveryDiagram.png
│   │   ├── MemoryLayoutDiagram.png
│   │   ├── MonitoringAndMetricsDiagram.png
│        ├── PartialDatabaseDesignDiagram.png
│   │   ├── StrategyGenerationPipelineDiagram.png
│   │   └── TestingDiagram.png
│   ├── DOCX files/
│       ├── Directory_Structure.docx
│        ├── KnowledgeGuide.docx
│        ├── OptimisationsGuide.docx
│        ├── Phase1_RoadMap.docx
│        └── Project_Idea.docx
│   ├── Environment.md
│    ├── FileStructure.md
│   ├── Idea.md
│   ├── Knowledge.md
│   ├── Optimisations.md
│   └── Roadmap1.md
├── Scripts/
├── .env
├── .gitignore
├── README.md
└── setup.sh
```