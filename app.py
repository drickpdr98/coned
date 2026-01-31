import streamlit as st
import pandas as pd

st.set_page_config(page_title="ConEd Usage Analyzer", layout="centered")
st.title("⚡ Con Edison Usage & Bill Estimator")
st.write("Upload your ConEd CSV file to see your usage and cost.")

file = st.file_uploader("Upload CSV", type=["csv"])

# NYC Rates
SUPPLY_RATE = 0.13
DELIVERY_RATE = 0.10
OTHER_FEES = 7

if file:
    df = pd.read_csv(file)

    # Detect usage column
    usage_col = None
    for col in df.columns:
        if "kwh" in col.lower() or "usage" in col.lower():
            usage_col = col
            break

    if not usage_col:
        st.error("Could not find kWh column.")
    else:
        # --- Ensure Date column exists ---
        if 'Date' in df.columns:
            # Parse date, ignore time
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
            # Remove invalid dates
            df = df.dropna(subset=['Date'])
            
            # Sum usage per day
            daily_usage = df.groupby('Date')[usage_col].sum().reset_index()
            
            # Number of unique days is now length of daily_usage
            total_days = len(daily_usage)
        else:
            # If no date column, just count rows
            total_days = len(df)
            daily_usage = df[[usage_col]].copy()
            daily_usage['Date'] = range(1, total_days+1)

        # Calculate charges
        daily_usage['Supply_Charge'] = daily_usage[usage_col] * SUPPLY_RATE
        daily_usage['Delivery_Charge'] = daily_usage[usage_col] * DELIVERY_RATE
        daily_usage['Daily_Total'] = daily_usage['Supply_Charge'] + daily_usage['Delivery_Charge']

        total_kwh = daily_usage[usage_col].sum()
        total_supply = daily_usage['Supply_Charge'].sum()
        total_delivery = daily_usage['Delivery_Charge'].sum()
        total_bill = total_supply + total_delivery + OTHER_FEES

        st.success("File Uploaded and Calculated!")

        st.metric("Total Usage (kWh)", round(total_kwh, 2))
        st.metric("Number of Days Used", total_days)
        st.metric("Supply Charges ($)", f"${round(total_supply, 2)}")
        st.metric("Delivery Charges ($)", f"${round(total_delivery, 2)}")
        st.metric("Other Fees ($)", f"${OTHER_FEES}")
        st.metric("Estimated Total Bill ($)", f"${round(total_bill, 2)}")

        # Daily usage chart
        st.subheader("📅 Daily Usage")
        st.line_chart(daily_usage.set_index('Date')[usage_col])

        # Raw data
        st.subheader("📄 Raw Data")
        st.dataframe(daily_usage)
