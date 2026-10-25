# SuperKart deployment with GitHub, GitHub Pages, and Render

## The important distinction

GitHub is the source-code repository. GitHub Pages can publish the **static interactive HTML dashboard**. GitHub Pages does not run Python, Flask, Streamlit, or the serialized Random Forest. For live predictions, connect the GitHub repository to a web host. This guide uses Render for the Flask API and Streamlit interface. GitHub Pages supports publishing from a repository branch/folder or a GitHub Actions workflow; Render can connect to a Git provider and auto-deploy from a chosen branch. [1] [2]

The delivered GitHub-ready ZIP already puts the dashboard at `docs/index.html`, includes the backend and frontend folders, and adjusts both Docker services to listen on Render’s `PORT` (default 10000) while binding to `0.0.0.0`. [3]

## 1. Extract and review the GitHub-ready project

Download and extract `SuperKart_GitHub_Render_Deployment_Bundle.zip`. It contains:

```text
README.md
GitHub_Render_Deployment_Guide.md
SHAP_Interpretation.md
.gitignore
docs/
  index.html                 # interactive dashboard for GitHub Pages
  .nojekyll
backend_files/
  app.py                      # Flask API: /health and /predict
  model.joblib                # fitted preprocessing + Random Forest pipeline
  requirements.txt
  Dockerfile
frontend_files/
  app.py                      # Streamlit prediction form
  requirements.txt
  Dockerfile
artifacts/
  model_metadata.json
```

The dashboard has embedded held-out predictions and SHAP examples. A public GitHub repository or Pages site makes that embedded sample public. The repository also contains the serialized model, so anyone with repository access can download it. Do not publish these files if they contain information you are not authorized to disclose. Never commit `.env` files, passwords, tokens, private keys, or customer records.

## 2. Create and push the GitHub repository

Create a new GitHub repository named something like `superkart-model-deployment`. If using GitHub Free and you want to use GitHub Pages, the repository generally needs to be public. Pages sites are public to visitors even in cases where a plan allows a private source repository. [4]

Open a terminal in the extracted bundle folder and replace `<YOUR_GITHUB_USERNAME>` with your account name:

```bash
git init
git add .
git commit -m "Add SuperKart model deployment and dashboard"
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/superkart-model-deployment.git
git push -u origin main
```

If you create the repository with a README or license already in GitHub, either clone it first and copy the bundle contents into that clone, or reconcile the histories before pushing. The simpler route is to create an empty repository, then push these files.

The API model artifact is about 16 MB. That size is under GitHub’s normal single-file blocking threshold, but it makes the repository larger. If the model grows substantially, use Git Large File Storage or external artifact storage and update the backend path/load step.

## 3. Publish the interactive dashboard with GitHub Pages

In the repository, open **Settings → Pages**. Under **Build and deployment**, select **Deploy from a branch**. Choose branch `main` and folder `/docs`, then save. GitHub Pages looks for an entry file such as `index.html` at the root of the publishing folder. [1] [5]

After the Pages build finishes, open the URL shown in Pages settings. For a project repository it will usually look like:

```text
https://<YOUR_GITHUB_USERNAME>.github.io/superkart-model-deployment/
```

The dashboard is static and self-contained: its plots and embedded data work without a backend. Use the **Predictions** tab to filter holdout estimates by store or product type, inspect observed-versus-predicted charts and large errors, and download the filtered holdout subset as CSV. Use **SHAP drivers** for global importance, feature-value direction, and an additive local waterfall. Use **Deployment & output files** for the in-dashboard quick guide.

GitHub Pages does not host server-side Python applications. Its purpose here is only to serve the HTML/JavaScript dashboard. [4]

## 4. Deploy the Flask prediction API from GitHub to Render

Sign in to Render and connect your GitHub account. Create a **New → Web Service**, then select the repository and the `main` branch. Render supports deploying a web service from a connected Git repository and provides a Docker runtime for Dockerfile-based services. [2] [6]

Set these values in the service configuration:

- **Name:** `superkart-revenue-api` (or another available name).
- **Root Directory:** `backend_files`.
- **Runtime / Language:** Docker.
- **Dockerfile:** `Dockerfile` in the selected root directory.
- **Health check path:** `/health`.
- **Environment:** Render’s default `PORT` is `10000`; the supplied Docker command reads it automatically. Do not hard-code a different production port.

Deploy and wait for the service status to become **Live**. Render requires a public web service to bind to `0.0.0.0` and recommends using its `PORT` variable; the supplied GitHub-ready backend/Dockerfile does this. [3]

Copy the API’s Render URL, for example `https://superkart-revenue-api.onrender.com`, and test the health route:

```bash
curl https://<API_SERVICE>.onrender.com/health
```

Expected response:

```json
{"model_loaded":true,"status":"ok"}
```

Test a prediction with a row using supported feature names:

```bash
curl -X POST https://<API_SERVICE>.onrender.com/predict \
  -H 'Content-Type: application/json' \
  -d '{"Product_Weight":13.79,"Product_Sugar_Content":"Low Sugar","Product_Allocated_Area":0.124,"Product_Type":"Dairy","Product_MRP":133.55,"Store_Id":"OUT004","Store_Establishment_Year":2009,"Store_Size":"Medium","Store_Location_City_Type":"Tier 2","Store_Type":"Supermarket Type2","Product_Id_Prefix":"FD"}'
```

A successful response includes a numeric `predictions` array. `Product_Id_Prefix` may alternatively be derived by the API from a `Product_Id` field. The deployed endpoint is publicly reachable and has no authentication or rate limiting by default; treat it as a demonstration endpoint, not a hardened production service.

## 5. Deploy the Streamlit prediction interface from GitHub to Render

Create another **Web Service** from the same GitHub repository and `main` branch. Set **Root Directory** to `frontend_files`, choose **Docker**, and deploy. The Streamlit Dockerfile also listens on Render’s assigned `PORT`.

In the new frontend service’s Render **Environment** settings, add:

```text
BACKEND_URL=https://<API_SERVICE>.onrender.com
```

Use the API base URL only. Do **not** append `/predict`; the Streamlit app adds that route. Save the variable and redeploy if Render does not redeploy automatically. Open the frontend’s `onrender.com` URL, enter product inputs, choose a store, and submit. The app derives the selected store’s profile attributes so the request is internally consistent.

The frontend makes its API request server-side, so browser CORS configuration is not required for this Streamlit-to-Flask connection. The static dashboard remains separate from the live prediction form.

## 6. Verify links and use the output files

Record these links only after testing each endpoint/page:

- **GitHub repository:** `https://github.com/<YOUR_GITHUB_USERNAME>/superkart-model-deployment`
- **Dashboard (GitHub Pages):** `https://<YOUR_GITHUB_USERNAME>.github.io/superkart-model-deployment/`
- **Flask API:** `https://<API_SERVICE>.onrender.com`
- **Streamlit estimator:** `https://<FRONTEND_SERVICE>.onrender.com`

Use `docs/index.html` for the interactive holdout/SHAP dashboard; it does not run new predictions. Use `frontend_files/app.py` at the Render frontend URL for new estimates. Use `backend_files/app.py` and `backend_files/model.joblib` as the API service. Keep `artifacts/model_metadata.json` with the deployment record for the model name, inputs, chosen parameters, and validation metrics. Use the notebooks and `SuperKart.csv` only when reproducing or retraining the analysis; they are not needed for inference once the model artifact is deployed.

The trained model uses NumPy 2.0.2, pandas 2.2.2, scikit-learn 1.6.1, and joblib 1.4.2 under Python 3.12. Preserve those package pins when loading the serialized pipeline unless you retrain and validate a replacement. The holdout result is **RMSE 294.69**, **MAE 107.58**, and **R² 0.925** across 1,753 held-out product-store rows.

## 7. Understand the SHAP drivers

SHAP contributions are expressed in the target’s revenue units. A positive SHAP value raises a record’s estimate relative to the model baseline; a negative value lowers it. Mean absolute SHAP measures typical influence magnitude, not whether a feature is always positive or negative.

`Product_MRP` is the largest individual driver, with mean absolute SHAP of about **409.7**. Across the 800-record explanation sample, the lowest MRP quintile (mean MRP about 107) has an average MRP contribution near **−504**, while the highest quintile (mean MRP about 191) is near **+543**. This shows the fitted model generally associates higher MRP with higher predicted record revenue, with a nonlinear pattern. It is not causal evidence that changing MRP alone will increase revenue.

`Product_Weight` is the next-largest single numeric driver, with mean absolute SHAP around **152.1**. In the same sample, the lightest weight quintile averages about **−138**, and the heaviest about **+246**. Weight may also be serving as a proxy for product or package characteristics that are not represented separately.

Store profile variables are important but redundant: the dataset has four store IDs, and each store’s ID is coupled with its store type, city tier, size, and establishment year. In the 800-record SHAP sample, the **sum** of those five contributions has mean absolute magnitude around **499.5**. The mean summed context is approximately **+1,203** for OUT003 and **−1,533** for OUT002. Interpret this as a joint learned outlet-profile difference, not an independent causal effect of store format, size, or location. With only four outlets, extrapolation to new stores is particularly uncertain.

Product type, sugar label, and product-ID prefix have much smaller per-record SHAP contributions after the model accounts for MRP, weight, and store profile. This does not contradict a category having the largest total historical revenue: total revenue also depends on how many records/items occur in that category. The data is cross-sectional and lacks transaction dates, stockouts, promotions, units sold, and margin; the model estimates one product-store row, not a validated quarterly forecast. Captum integrated gradients is not appropriate for this scikit-learn Random Forest; SHAP/TreeSHAP is the relevant tree-model attribution method used here.

## Troubleshooting

- **Pages shows a 404:** confirm `docs/index.html` exists on `main`, and Pages is configured to publish `main` → `/docs`. Check the Pages deployment status in the Actions tab.
- **Render build cannot find the Dockerfile/model:** confirm Root Directory points to the relevant app folder and that folder contains its `Dockerfile`, `app.py`, `requirements.txt`, and, for the backend, `model.joblib`.
- **API deploy fails its port check:** verify the GitHub-ready Dockerfile uses `PORT` with fallback `10000` and binds to `0.0.0.0`. Render routes inbound traffic to the assigned public HTTP port. [3]
- **Frontend reports a backend connection error:** verify `BACKEND_URL` is the API’s exact HTTPS service URL, that `/health` works, and that the Streamlit service was redeployed after setting the environment variable.
- **First request is slow:** Render’s free web services may spin down after inactivity and take time to start again. Check the current free-plan behavior in Render’s documentation before relying on response-time guarantees. [2]

## References

[1]: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site "Configuring a publishing source for GitHub Pages"
[2]: https://render.com/docs/your-first-deploy "Your first Render deploy"
[3]: https://render.com/docs/web-services "Render web services and port binding"
[4]: https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site "Creating a GitHub Pages site"
[6]: https://render.com/docs/docker "Docker on Render"
