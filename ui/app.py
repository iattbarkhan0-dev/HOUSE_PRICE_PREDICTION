import streamlit as st
import requests
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="House Price Prediction",
    page_icon="🏠",
    layout="wide"
)


# ============================================================
# API HELPER FUNCTIONS
# ============================================================

def get_api(endpoint):
    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=10
        )
        return response

    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to FastAPI: {e}")
        return None


def post_api(endpoint, params=None, json_data=None):
    try:
        response = requests.post(
            f"{API_URL}{endpoint}",
            params=params,
            json=json_data,
            timeout=10
        )
        return response

    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to FastAPI: {e}")
        return None


# ============================================================
# PAGE TITLE
# ============================================================

st.title("🏠 House Price Prediction")
st.caption(
    "California Housing Price Prediction • "
    "Model Versioning • A/B Testing • Performance Monitoring"
)


# ============================================================
# HOUSE PRICE PREDICTION
# ============================================================

st.header("💰 Predict House Price")

st.write(
    "Enter the house details below. The prediction will be "
    "sent to the FastAPI backend and routed through the "
    "active model or A/B testing system."
)

with st.form("prediction_form"):

    col1, col2, col3 = st.columns(3)

    with col1:
        longitude = st.number_input(
            "Longitude",
            value=-122.23,
            format="%.4f"
        )

        latitude = st.number_input(
            "Latitude",
            value=37.88,
            format="%.4f"
        )

        housing_median_age = st.number_input(
            "Housing Median Age",
            min_value=1.0,
            value=41.0,
            step=1.0
        )

    with col2:
        total_rooms = st.number_input(
            "Total Rooms",
            min_value=1.0,
            value=880.0,
            step=1.0
        )

        total_bedrooms = st.number_input(
            "Total Bedrooms",
            min_value=1.0,
            value=129.0,
            step=1.0
        )

        population = st.number_input(
            "Population",
            min_value=1.0,
            value=322.0,
            step=1.0
        )

    with col3:
        households = st.number_input(
            "Households",
            min_value=1.0,
            value=126.0,
            step=1.0
        )

        median_income = st.number_input(
            "Median Income",
            min_value=0.01,
            value=8.3252,
            step=0.1,
            format="%.4f"
        )

        ocean_proximity = st.selectbox(
            "Ocean Proximity",
            [
                "<1H OCEAN",
                "INLAND",
                "ISLAND",
                "NEAR BAY",
                "NEAR OCEAN"
            ]
        )

    predict_button = st.form_submit_button(
        "🏠 Predict House Price",
        use_container_width=True
    )


# ============================================================
# SEND PREDICTION REQUEST
# ============================================================

if predict_button:

    house_data = {
        "longitude": longitude,
        "latitude": latitude,
        "housing_median_age": housing_median_age,
        "total_rooms": total_rooms,
        "total_bedrooms": total_bedrooms,
        "population": population,
        "households": households,
        "median_income": median_income,
        "ocean_proximity": ocean_proximity
    }

    response = post_api(
        "/predict",
        json_data=house_data
    )

    if response is not None:

        if response.status_code == 200:

            result = response.json()

            st.success("House price prediction completed successfully.")

            st.subheader("Prediction Result")

            result_col1, result_col2, result_col3 = st.columns(3)

            with result_col1:
                st.metric(
                    "Predicted House Price",
                    f"${result['prediction']:,.2f}"
                )

            with result_col2:
                st.metric(
                    "Model Used",
                    result["model_version"]
                )

            with result_col3:
                st.metric(
                    "Prediction ID",
                    result["prediction_id"]
                )

            st.write("Prediction Details")

            st.json(result)

            # Store prediction information for actual-price entry
            st.session_state["prediction_id"] = result[
                "prediction_id"
            ]

            st.session_state["prediction"] = result[
                "prediction"
            ]

            st.session_state["prediction_model"] = result[
                "model_version"
            ]

        else:

            st.error(
                f"Prediction failed. "
                f"API returned {response.status_code}: "
                f"{response.text}"
            )


# ============================================================
# ACTUAL PRICE
# ============================================================

st.header("📌 Enter Actual House Price")

if "prediction_id" not in st.session_state:

    st.info(
        "First make a house price prediction. "
        "Then enter the actual selling price here."
    )

else:

    st.write(
        f"Prediction ID: **{st.session_state['prediction_id']}**"
    )

    st.write(
        f"Model Used: **{st.session_state['prediction_model']}**"
    )

    st.write(
        f"Predicted Price: "
        f"**${st.session_state['prediction']:,.2f}**"
    )

    actual_price = st.number_input(
        "Actual Selling Price",
        min_value=1.0,
        value=st.session_state["prediction"],
        step=1000.0
    )

    if st.button(
        "Submit Actual Price",
        use_container_width=True
    ):

        actual_price_data = {
            "prediction_id": st.session_state[
                "prediction_id"
            ],
            "actual_price": actual_price
        }

        response = post_api(
            "/actual-price",
            json_data=actual_price_data
        )

        if response is not None:

            if response.status_code == 200:

                result = response.json()

                st.success(
                    "Actual price recorded successfully."
                )

                col1, col2 = st.columns(2)

                with col1:
                    st.metric(
                        "Prediction",
                        f"${result['prediction']:,.2f}"
                    )

                with col2:
                    st.metric(
                        "Absolute Error",
                        f"${result['absolute_error']:,.2f}"
                    )

                st.json(result)

            else:

                st.error(
                    f"Could not record actual price. "
                    f"API returned {response.status_code}: "
                    f"{response.text}"
                )


# ============================================================
# ADMIN PANEL
# ============================================================

st.divider()

st.title("⚙️ House Price Model Admin Panel")

st.caption(
    "Model Versioning • A/B Testing • "
    "Performance Monitoring • Rollback"
)


# ============================================================
# MODEL VERSIONS
# ============================================================

versions_response = get_api("/versions")

if versions_response is None:
    st.stop()

if versions_response.status_code != 200:

    st.error(
        f"Could not load model versions. "
        f"API returned {versions_response.status_code}: "
        f"{versions_response.text}"
    )

    st.stop()

versions = versions_response.json()

if not versions:

    st.warning(
        "No model versions found in database."
    )

    st.stop()

versions_df = pd.DataFrame(versions)

available_versions = versions_df[
    "version"
].tolist()


st.header("📦 Model Versions")

display_columns = [
    "version",
    "mae",
    "rmse",
    "r2",
    "traffic_percentage",
    "is_active"
]

existing_columns = [
    column
    for column in display_columns
    if column in versions_df.columns
]

st.dataframe(
    versions_df[existing_columns],
    use_container_width=True,
    hide_index=True
)


# ============================================================
# ACTIVE MODEL
# ============================================================

st.header("🎯 Active Model")

active_response = get_api("/active")

active_version = None

if active_response is not None:

    if active_response.status_code == 200:

        active_version = active_response.json()[
            "active_version"
        ]

        st.success(
            f"Currently Active Model: {active_version}"
        )

    else:

        st.error(
            f"Could not get active model. "
            f"API returned {active_response.status_code}: "
            f"{active_response.text}"
        )


# ============================================================
# SWITCH ACTIVE MODEL
# ============================================================

st.header("🔄 Switch Active Model")

if active_version in available_versions:

    default_index = available_versions.index(
        active_version
    )

else:

    default_index = 0


selected_version = st.selectbox(
    "Select model version",
    available_versions,
    index=default_index,
    key="switch_version"
)


if st.button(
    "Switch Model",
    type="primary",
    use_container_width=True
):

    response = post_api(
        f"/switch/{selected_version}"
    )

    if response is not None:

        if response.status_code == 200:

            result = response.json()

            st.success(
                f"Active model changed to "
                f"{result.get('active_version', selected_version)}"
            )

            st.rerun()

        else:

            st.error(
                f"Model switch failed: "
                f"{response.text}"
            )


# ============================================================
# A/B TESTING
# ============================================================

st.header("🧪 A/B Testing")

ab_enabled = st.checkbox(
    "Enable A/B Testing",
    key="ab_enabled"
)


col1, col2 = st.columns(2)


with col1:

    if "v2" in available_versions:

        version1_default = available_versions.index(
            "v2"
        )

    else:

        version1_default = 0


    version1 = st.selectbox(
        "Version 1",
        available_versions,
        index=version1_default,
        key="ab_version1"
    )


with col2:

    if "v3" in available_versions:

        version2_default = available_versions.index(
            "v3"
        )

    elif len(available_versions) > 1:

        version2_default = 1

    else:

        version2_default = 0


    version2 = st.selectbox(
        "Version 2",
        available_versions,
        index=version2_default,
        key="ab_version2"
    )


percentage1 = st.slider(
    f"Traffic for {version1} (%)",
    min_value=0,
    max_value=100,
    value=50,
    step=5,
    key="percentage1"
)


percentage2 = 100 - percentage1


col1, col2 = st.columns(2)


with col1:

    st.metric(
        f"{version1} Traffic",
        f"{percentage1}%"
    )


with col2:

    st.metric(
        f"{version2} Traffic",
        f"{percentage2}%"
    )


if version1 == version2:

    st.warning(
        "Version 1 and Version 2 must be different."
    )

else:

    if st.button(
        "Configure A/B Testing",
        use_container_width=True
    ):

        params = {
            "enabled": ab_enabled,
            "version1": version1,
            "version2": version2,
            "percentage1": percentage1,
            "percentage2": percentage2
        }

        response = post_api(
            "/ab-testing",
            params=params
        )

        if response is not None:

            if response.status_code == 200:

                result = response.json()

                st.success(
                    "A/B testing configuration updated."
                )

                st.json(result)

            else:

                st.error(
                    f"A/B testing configuration failed: "
                    f"{response.text}"
                )


# ============================================================
# MODEL ROLLBACK
# ============================================================

st.header("↩️ Model Rollback")

rollback_version = st.selectbox(
    "Select model version to rollback to",
    available_versions,
    key="rollback_version"
)


if st.button(
    "Rollback Model",
    use_container_width=True
):

    response = post_api(
        f"/rollback/{rollback_version}"
    )

    if response is not None:

        if response.status_code == 200:

            result = response.json()

            st.success(
                f"Rollback successful. "
                f"Active model: "
                f"{result.get('active_version', rollback_version)}"
            )

            st.rerun()

        else:

            st.error(
                f"Rollback failed: {response.text}"
            )


# ============================================================
# LIVE PERFORMANCE
# ============================================================

st.header("📊 Live Model Performance")

performance_response = get_api(
    "/performance"
)


if performance_response is None:

    st.error(
        "Could not load performance data."
    )


elif performance_response.status_code != 200:

    st.error(
        f"Could not load performance data. "
        f"API returned "
        f"{performance_response.status_code}: "
        f"{performance_response.text}"
    )


else:

    performance = performance_response.json()

    if not performance:

        st.info(
            "No performance data available yet."
        )

    else:

        performance_df = pd.DataFrame(
            performance
        )

        st.dataframe(
            performance_df,
            use_container_width=True,
            hide_index=True
        )

        if "mae" in performance_df.columns:

            chart_data = (
                performance_df[
                    ["version", "mae"]
                ]
                .dropna()
            )

            if not chart_data.empty:

                chart_data = chart_data.set_index(
                    "version"
                )

                st.subheader(
                    "Live MAE Comparison"
                )

                st.bar_chart(
                    chart_data
                )

            else:

                st.info(
                    "Live MAE data is not available yet. "
                    "Submit actual prices for predictions first."
                )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "House Price Prediction | "
    "Model Versioning & Rollback System")