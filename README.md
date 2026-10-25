# SuperKart Random Forest model deployment

This repository provides an interactive static dashboard plus a deployable Flask API and Streamlit inference UI.

- **Interactive dashboard:** `docs/index.html` — publish with GitHub Pages from `main` → `/docs`.
- **Live prediction API:** `backend_files/` — deploy from this GitHub repository as a Render Docker Web Service with Root Directory `backend_files`.
- **Live Streamlit estimator:** `frontend_files/` — deploy as a second Render Docker Web Service with Root Directory `frontend_files`; set `BACKEND_URL` to the API service's HTTPS base URL.
- **Model metadata:** `artifacts/model_metadata.json`.
- **SHAP interpretation:** [SHAP_Interpretation.md](SHAP_Interpretation.md).
- **Complete deployment steps:** [GitHub_Render_Deployment_Guide.md](GitHub_Render_Deployment_Guide.md).

GitHub is used for source control and Pages hosting. GitHub Pages only serves the HTML dashboard; it does not run Flask, Streamlit, or Python inference. Render runs the API and UI, and will deploy new commits from the configured Git branch.

The model predicts revenue for one product-store record. On the saved holdout, it achieved RMSE 294.69, MAE 107.58, and R² 0.925. These are row-level validation metrics, not quarter-ahead forecasting metrics. The data has no transaction dates and contains only four stores, so do not treat store SHAP attributions as independent causal effects or assume the model generalizes to unseen outlets.

## Security and visibility

This starter repository includes a serialized model. If the GitHub repository or Pages site is public, anyone can read and download public repository files and visit the dashboard. The dashboard embeds holdout prediction and SHAP samples. Confirm that you are allowed to publish them. Do not commit passwords, access tokens, API keys, or private records. The demo API has no authentication or rate limiting by default; add appropriate controls before production use.

## Update/deploy cycle

Edit files, commit, and push to the connected branch. GitHub Pages republishes the dashboard when `docs/` changes. Render can auto-deploy each connected service when files in its configured app root change on the selected branch. Review build logs if a deployment fails.
