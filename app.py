import streamlit as st
import pandas as pd

st.set_page_config(page_title="ConEd Usage Analyzer", layout="centered")
st.title("⚡ Con Edison Usage & Bill Estimator")
st.write("Upload your ConEd CSV file to see your usage and cost.")

# --- Upload CSV ---
file = st.file_uploader("Upload CSV", type=["csv"])

# --- NYC Rates (adjust as needed) ---
SUPPLY_RATE = 0.13       # $ per kWh
DELIVERY_RATE = 0.10     # $ per kWh
OTHER_FEES = 7           # $ flat monthly fees

if file:
    df = pd.read_csv(file)

    # Try to detect usage column
    usage_col = None
    for col in df.columns:
        if "kwh" in col.lower() or "usage" in col.lower():
            usage_col = col
            break

    if not usage_col:
        st.error("Could not find kWh column.")
    else:
        # Calculate charges
        df['Supply_Charge'] = df[usage_col] * SUPPLY_RATE
        df['Delivery_Charge'] = df[usage_col] * DELIVERY_RATE
        df['Daily_Total'] = df['Supply_Charge'] + df['Delivery_Charge']

        total_kwh = df[usage_col].sum()
        total_supply = df['Supply_Charge'].sum()
        total_delivery = df['Delivery_Charge'].sum()
        total_days = df['Date'].nunique() if 'Date' in df.columns else len(df)
        total_bill = total_supply + total_delivery + OTHER_FEES

        st.success("File Uploaded and Calculated!")

        # Display metrics
        st.metric("Total Usage (kWh)", round(total_kwh, 2))
        st.metric("Number of Days Used", total_days)
        st.metric("Supply Charges ($)", f"${round(total_supply, 2)}")
        st.metric("Delivery Charges ($)", f"${round(total_delivery, 2)}")
        st.metric("Other Fees ($)", f"${OTHER_FEES}")
        st.metric("Estimated Total Bill ($)", f"${round(total_bill, 2)}")

        # Daily summary chart
        if "Date" in df.columns:
            daily = df.groupby("Date")[usage_col].sum()
            st.subheader("📅 Daily Usage")
            st.line_chart(daily)

        # Raw data
        st.subheader("📄 Raw Data")
        st.dataframe(df)
