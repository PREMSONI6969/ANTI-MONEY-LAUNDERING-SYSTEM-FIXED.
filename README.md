# ClearTrace — Anti-Money-Laundering Detection

A Flask web interface for the included CatBoost classifier. Upload a compatible preprocessed CSV and download the results with an `isFraud` prediction column.

## Features
- Responsive upload interface
- CSV upload (no server-side local filepath input)
- Input validation, file-size limit, and downloadable output
- Health endpoint at `/health`
- Render deployment configuration (`render.yaml`)
- No external Google Drive upload or hard-coded credentials

## Run locally

Python 3.10 or 3.11 is recommended for this legacy serialized model.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`. Check `http://127.0.0.1:5000/health` for service status.

## Input format

The included model expects the **preprocessed feature set**, not the original raw PaySim dataset. Required columns are:

`segment`, `step`, `trans_type`, `amount`, `nameOrig`, `oldbalanceOrg`, `nameDest`, `oldbalanceDest`, `accountType`

The preprocessing scripts expect source data under `data/` and intermediate files under `data_processed/`; those datasets are not bundled. Prepare the data using the project's original pipeline before uploading. Column names and categorical values must match the training pipeline.

## Deploy to Render

1. Push this project to a GitHub repository you own.
2. In Render, choose **New + → Blueprint** and select that repository.
3. Render reads `render.yaml`, installs `requirements.txt`, and starts Gunicorn.
4. Wait for the deploy to finish and verify `/health`.

The deployment platform creates the public URL; it cannot be created from this archive alone without access to your GitHub/hosting account. Never commit credentials or real transaction data.

## Security and limitations
- The original app included a hard-coded Google API bearer token. It has been removed; if it was ever valid, revoke it immediately and use a newly issued secret only if external storage is genuinely needed.
- Pickle files can execute code when loaded. Only use the model file from a trusted source.
- This model is an educational prototype and must not be used as the sole basis for AML compliance decisions.
