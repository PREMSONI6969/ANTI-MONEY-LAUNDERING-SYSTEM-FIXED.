"""AML transaction risk scoring web application."""
from __future__ import annotations

import io
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "saved_models" / "model.pkl"
ALLOWED_EXTENSIONS = {"csv"}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# This model was trained on the transformed feature set produced by the project's
# preprocessing pipeline, not on the original unprocessed PaySim CSV.
REQUIRED_COLUMNS = [
    "segment", "step", "trans_type", "amount", "nameOrig",
    "oldbalanceOrg", "nameDest", "oldbalanceDest", "accountType",
]

_model = None

def get_model():
    global _model
    if _model is None:
        if not MODEL_PATH.is_file():
            raise RuntimeError("The trained model is missing from saved_models/model.pkl.")
        with MODEL_PATH.open("rb") as model_file:
            _model = pickle.load(model_file)
    return _model

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/predict")
def predict():
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return render_template("index.html", error="Choose a CSV file before running a prediction."), 400
    filename = secure_filename(uploaded.filename)
    if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        return render_template("index.html", error="Only .csv files are supported."), 400

    try:
        data = pd.read_csv(uploaded, low_memory=False)
        if data.empty:
            raise ValueError("The uploaded CSV contains no rows.")
        missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
        if missing:
            raise ValueError(
                "This model requires the project's preprocessed CSV. Missing columns: "
                + ", ".join(missing)
                + ". Run the preprocessing pipeline first; the original raw PaySim file is not directly compatible."
            )
        model_input = data[REQUIRED_COLUMNS].copy()
        predictions = get_model().predict(model_input)
        data["isFraud"] = np.asarray(predictions).reshape(-1).astype(int)
        output = io.BytesIO()
        data.to_csv(output, index=False)
        output.seek(0)
        output_name = f"aml_predictions_{pd.Timestamp.now(tz='UTC').strftime('%Y%m%d_%H%M%S')}.csv"
        return send_file(output, mimetype="text/csv", as_attachment=True, download_name=output_name)
    except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
        return render_template("index.html", error=str(exc)), 400
    except Exception:
        app.logger.exception("Prediction failed")
        return render_template(
            "index.html",
            error="Prediction failed while loading the model or processing this file. Check that the model and dependencies are compatible.",
        ), 500

@app.errorhandler(413)
def too_large(_error):
    return render_template("index.html", error="File is too large. Maximum upload size is 50 MB."), 413

@app.get("/health")
def health():
    return {"status": "ok", "model_file_present": MODEL_PATH.is_file()}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port= int(__import__("os").environ.get("PORT", "5000")), debug=False)
