import streamlit as st
import pandas as pd

st.set_page_config(page_title="ConEd Usage Analyzer", layout="centered")

st.title("⚡ Con Edison Usage & Bill Estimator")

st.write("Upload your ConEd CSV file to see your usage and cost.")

# Upload
file = st.file_uploader("Upload CSV", type=["csv"])

RATE = 0.27  # Your average $/kWh

if file:
    df = pd.read_csv(file)

    # Try to find usage column
    usage_col = None

    for col in df.columns:
        if "kwh" in col.lower() or "usage" in col.lower():
            usage_col = col
            break

    if not usage_col:
        st.error("Could not find kWh column.")
    else:
        total_kwh = df[usage_col].sum()
        est_bill = total_kwh * RATE

        st.success("File Uploaded!")

        st.metric("Total Usage (kWh)", round(total_kwh, 2))
        st.metric("Estimated Bill ($)", f"${round(est_bill, 2)}")

        # Daily summary
        if "Date" in df.columns:
            daily = df.groupby("Date")[usage_col].sum()

            st.subheader("📅 Daily Usage")
            st.line_chart(daily)

        # Raw data
        st.subheader("📄 Raw Data")
        st.dataframe(df)
