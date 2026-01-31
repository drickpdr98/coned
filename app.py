import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="ConEd Usage Analyzer", layout="centered")

st.markdown(
    "<h1 style='text-align: center;'>⚡ Con Edison Electricity Usage & Full Bill Estimator (Supply + Delivery + Taxes)</h1>",
    unsafe_allow_html=True
)
st.write("Upload your ConEd CSV file; the app will automatically filter the data we need.")

file = st.file_uploader("Upload CSV", type=["csv"])

# --- Supply and Delivery rates ---
SUPPLY_RATE = 0.11736
MERCHANT_FUNCTION_CHARGE = 3.36
SUPPLY_GRT_OTHER = 2.61
SUPPLY_SALES_TAX_RATE = 0.045

BASIC_SERVICE_CHARGE = 21.28
DELIVERY_RATE = 0.17192
SYSTEM_BENEFIT_CHARGE = 0.00453
DELIVERY_GRT_OTHER = 8.60
DELIVERY_SALES_TAX_RATE = 0.045

if file:
    try:
        # --- Read all lines from uploaded file ---
        stringio = StringIO(file.getvalue().decode("utf-8"))
        lines = stringio.readlines()
        
        # --- Find first row with actual usage data ---
        start_row = 0
        for i, line in enumerate(lines):
            if "IMPORT" in line.upper() and "KWH" in line.upper():
                start_row = i
                break
        
        # --- Read CSV from that row ---
        stringio.seek(0)  # reset pointer
        df_raw = pd.read_csv(stringio, skiprows=start_row)
        
        # --- Keep only Date + usage columns ---
        usage_col_candidates = [col for col in df_raw.columns if "import" in col.lower() and "kwh" in col.lower()]
        date_col_candidates = [col for col in df_raw.columns if "date" in col.lower()]
        
        if not usage_col_candidates:
            st.error("Could not find a usage column like 'Import (kWh)'.")
        elif not date_col_candidates:
            st.error("Could not find a Date column.")
        else:
            usage_col = usage_col_candidates[0]
            date_col = date_col_candidates[0]
            
            df = df[[date_col, usage_col]].copy()
            df.rename(columns={date_col: '15 Min Interval'}, inplace=True)

            # --- Convert datetime and aggregate per day ---
            df['DateTime'] = pd.to_datetime(df['15 Min Interval'], errors='coerce')
            df = df.dropna(subset=['DateTime'])
            df['Date'] = df['DateTime'].dt.date

            daily_usage = df.groupby('Date')[usage_col].sum().reset_index()
            total_days = len(daily_usage)

            # --- Calculate Supply ---
            daily_usage['Supply_Charge'] = daily_usage[usage_col] * SUPPLY_RATE
            total_supply = daily_usage['Supply_Charge'].sum()
            total_supply_with_fixed = total_supply + MERCHANT_FUNCTION_CHARGE + SUPPLY_GRT_OTHER
            supply_sales_tax = total_supply_with_fixed * SUPPLY_SALES_TAX_RATE
            total_supply_bill = total_supply_with_fixed + supply_sales_tax

            # --- Calculate Delivery ---
            daily_usage['Delivery_Charge'] = daily_usage[usage_col] * DELIVERY_RATE
            daily_usage['System_Benefit_Charge'] = daily_usage[usage_col] * SYSTEM_BENEFIT_CHARGE
            total_delivery = (
                daily_usage['Delivery_Charge'].sum() +
                daily_usage['System_Benefit_Charge'].sum() +
                BASIC_SERVICE_CHARGE +
                DELIVERY_GRT_OTHER
            )
            delivery_sales_tax = total_delivery * DELIVERY_SALES_TAX_RATE
            total_delivery_bill = total_delivery + delivery_sales_tax

            total_kwh = daily_usage[usage_col].sum()
            total_bill = total_supply_bill + total_delivery_bill

            st.success("File Uploaded and Calculated!")

            st.metric("Total Usage (kWh)", round(total_kwh, 2))
            st.metric("Number of Days Used", total_days)
            st.metric("Supply Charges ($)", f"${round(total_supply_bill, 2)}")
            st.metric("Delivery Charges ($)", f"${round(total_delivery_bill, 2)}")
            st.metric("Estimated Total Bill ($)", f"${round(total_bill, 2)}")

            st.subheader("📅 Daily Usage (summed from 15-min intervals)")
            st.line_chart(daily_usage.set_index('Date')[usage_col])

            st.subheader("📄 Daily Aggregated Data")
            st.dataframe(daily_usage)

    except Exception as e:
        st.error(f"Failed to read CSV: {e}")

# --- Footer ---
st.markdown(
    "<hr><p style='text-align:center;font-size:14px;'>Created by Dravin S | Email: dravin.drickpaul2@gmail.com</p>",
    unsafe_allow_html=True
)
