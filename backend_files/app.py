"""SuperKart prediction API.

The API loads the saved preprocessing + Random Forest pipeline once at startup,
then exposes a health check and JSON prediction endpoint. Render supplies PORT;
local development falls back to port 10000.
"""
import os
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, request

app = Flask(__name__)

# Keep model artifact beside this file so the same folder can be deployed as a
# Render monorepo root directory without relying on the caller's working path.
MODEL_PATH = Path(__file__).resolve().parent / "model.joblib"
MODEL = joblib.load(MODEL_PATH)

# Keep input field order aligned with the preprocessing pipeline used in training.
FEATURES = [
    "Product_Weight",
    "Product_Sugar_Content",
    "Product_Allocated_Area",
    "Product_Type",
    "Product_MRP",
    "Store_Id",
    "Store_Establishment_Year",
    "Store_Size",
    "Store_Location_City_Type",
    "Store_Type",
    "Product_Id_Prefix",
]
REQUIRED = [field for field in FEATURES if field != "Product_Id_Prefix"]


@app.get("/health")
def health():
    """Return a small readiness response for Render's health check."""
    return jsonify({"status": "ok", "model_loaded": MODEL is not None})


@app.post("/predict")
def predict():
    """Return one estimate per input JSON row; reject malformed/missing inputs."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, (dict, list)):
        return jsonify({"error": "Send a JSON object or a list of JSON objects."}), 400

    rows = payload if isinstance(payload, list) else [payload]
    try:
        frame = pd.DataFrame(rows)
        # Support callers that have the complete item ID instead of its family.
        if "Product_Id_Prefix" not in frame.columns:
            if "Product_Id" not in frame.columns:
                raise ValueError("Provide Product_Id_Prefix (FD, DR, or NC) or Product_Id.")
            frame["Product_Id_Prefix"] = frame["Product_Id"].astype(str).str[:2]

        missing = [field for field in REQUIRED if field not in frame.columns]
        if missing:
            raise ValueError("Missing required fields: " + ", ".join(missing))

        # Normalize a common source-data abbreviation before preprocessing.
        frame["Product_Sugar_Content"] = frame["Product_Sugar_Content"].replace({"reg": "Regular"})
        predictions = MODEL.predict(frame[FEATURES]).tolist()
        return jsonify({"predictions": predictions, "count": len(predictions)})
    except (ValueError, TypeError, KeyError) as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    # Render routes to PORT, usually 10000; the fallback supports local testing.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
