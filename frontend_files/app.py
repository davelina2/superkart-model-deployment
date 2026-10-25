"""Streamlit UI for the SuperKart row-level revenue estimator.

This frontend sends prediction requests from the server to the separately
hosted Flask API. Configure BACKEND_URL on the Render frontend service.
"""
import os

import requests
import streamlit as st

st.set_page_config(page_title="SuperKart Revenue Estimator", page_icon="📈", layout="centered")
st.title("SuperKart Product-Store Revenue Estimator")
st.caption("Estimates revenue for one product-store record. This is not a quarter-level forecast.")

# Set this in the Render frontend service's Environment settings, without /predict.
backend_url = os.getenv("BACKEND_URL", "").strip().rstrip("/")

# Store attributes are selected as one known profile so the form cannot submit
# contradictory combinations of store ID, format, size, city tier, and year.
STORE_PROFILES = {
    "OUT001": {
        "Store_Establishment_Year": 1987,
        "Store_Size": "High",
        "Store_Location_City_Type": "Tier 2",
        "Store_Type": "Supermarket Type1",
    },
    "OUT002": {
        "Store_Establishment_Year": 1998,
        "Store_Size": "Small",
        "Store_Location_City_Type": "Tier 3",
        "Store_Type": "Food Mart",
    },
    "OUT003": {
        "Store_Establishment_Year": 1999,
        "Store_Size": "Medium",
        "Store_Location_City_Type": "Tier 1",
        "Store_Type": "Departmental Store",
    },
    "OUT004": {
        "Store_Establishment_Year": 2009,
        "Store_Size": "Medium",
        "Store_Location_City_Type": "Tier 2",
        "Store_Type": "Supermarket Type2",
    },
}

# Collect model inputs in one form; the target is a record-level revenue estimate.
with st.form("prediction_form"):
    col_left, col_right = st.columns(2)
    with col_left:
        weight = st.number_input("Product weight", min_value=0.01, value=12.0)
        allocated_area = st.number_input("Allocated display area", min_value=0.0, value=0.05, step=0.01)
        mrp = st.number_input("Product MRP", min_value=0.01, value=150.0)
        product_prefix = st.selectbox("Product ID family", ["FD", "DR", "NC"])
        product_type = st.selectbox(
            "Product type",
            [
                "Fruits and Vegetables", "Snack Foods", "Dairy", "Frozen Foods",
                "Household", "Baking Goods", "Canned", "Health and Hygiene",
                "Meat", "Soft Drinks", "Breads", "Hard Drinks", "Others",
                "Starchy Foods", "Breakfast", "Seafood",
            ],
        )
    with col_right:
        sugar = st.selectbox("Sugar content", ["Low Sugar", "Regular", "No Sugar"])
        store_id = st.selectbox("Store ID", list(STORE_PROFILES))
    submitted = st.form_submit_button("Estimate revenue")

store_profile = STORE_PROFILES[store_id]
st.caption(
    f"Selected profile: {store_profile['Store_Type']} | "
    f"{store_profile['Store_Size']} | {store_profile['Store_Location_City_Type']}"
)

if submitted:
    if not backend_url:
        st.error("Set BACKEND_URL in the Render frontend service's Environment settings first.")
    else:
        # Build a schema-aligned request body, adding the store fields from its profile.
        body = {
            "Product_Weight": weight,
            "Product_Sugar_Content": sugar,
            "Product_Allocated_Area": allocated_area,
            "Product_Type": product_type,
            "Product_MRP": mrp,
            "Store_Id": store_id,
            **store_profile,
            "Product_Id_Prefix": product_prefix,
        }
        try:
            response = requests.post(f"{backend_url}/predict", json=body, timeout=30)
            response.raise_for_status()
            estimate = response.json()["predictions"][0]
            st.metric("Estimated product-store revenue", f"{estimate:,.2f}")
        except requests.RequestException as exc:
            st.error(f"Backend request failed: {exc}")
