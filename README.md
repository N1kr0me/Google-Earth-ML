# GEE-Flood

End-to-end satellite ML project using Google Earth Engine (GEE), PostgreSQL, PyTorch, and FastAPI.

This repo is designed as a CV-ready, interview-friendly project showing data engineering, ML training, MLOps structure, and API deployment.

## What this project does

- Queries satellite imagery via GEE and exports tiles for water/flood detection.
- Stores tile metadata and labels in PostgreSQL.
- Trains a baseline CNN classifier (water vs non-water / flood vs non-flood).
- Serves predictions via a secure FastAPI service with rate limiting.
- Runs in Docker and can be deployed to AWS.

## Repository layout

- `gee_flood/` Python package
  - `data/` GEE client, DB access, and tile metadata
  - `model/` training and inference
  - `api/` FastAPI service
- `config/` training config
- `scripts/` operational scripts and deployment notes
- `artifacts/` model outputs (created after training)

## Quickstart (Windows)

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Create a local `.env` file from the template:

```bash
copy .env.example .env
```

### Start Postgres + API (Docker)

```bash
docker compose up --build
```

## TODOs you must do (important for interviews)

- **GEE authentication and first data export**  
  Edit `gee_flood\data\gee_client.py` and run the auth/init flow. This proves you can securely access GEE and manage imagery exports.

- **Create and configure PostgreSQL**  
  Run the Docker database (or your own Postgres) and set credentials in `.env`. This shows you can manage data storage for ML pipelines.

- **Run training experiments**  
  Execute `gee_flood\model\train.py`, try different hyperparameters, and record metrics. This demonstrates real model tuning, not just a demo.

- **Build and deploy the API to AWS**  
  Follow `scripts\deploy_aws.md` and run the commands yourself. This is key proof of MLOps ownership.

## How to run training (after DB + data)

```bash
python -m gee_flood.model.train --config config\train_config.yaml
```

## How to run the API locally (after training)

```bash
uvicorn gee_flood.api.main:app --host 0.0.0.0 --port 8000
```

## Notes

- `docs_build_walkthrough.md` and `docs_interview_questions.md` are created for your personal prep and ignored by git.
- This repo intentionally contains TODOs that you must complete to make the project authentic and interview-ready.
