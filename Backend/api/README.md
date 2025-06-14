# FastAPI Backend Setup

## Prerequisites

Install the required system packages:
```bash
sudo apt install python3.10-venv python3-pip
```

## Setup

Run the setup script:
```bash
./setup_env.sh
```

Or manually:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the API

```bash
source venv/bin/activate
python main.py
```

The API will be available at http://localhost:8000
API documentation at http://localhost:8000/docs