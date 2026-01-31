import streamlit as st
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="ConEd Usage Analyzer", layout="centered")

# --- Centered Title in one long line ---
st.markdown(
    "<h1 style='text-align: center;'>⚡ Con Edison Electricity Usage & Full Bill Estimator (Supply + Delivery + Taxes)</h1>",
    unsafe_allow_html=True
)
st.write("Upload your ConEd CSV file with 15-minute interval data to see your usage and estimated cost.")

file = st.file_uploader("Upload CSV", type=["csv"])

# --- Supply components ---
SUPPLY_RATE = 0.11736                 # $ per kWh
MERCHANT_FUNCTION_CHARGE = 3.36       # $ fixed
SUPPLY_GRT_OTHER = 2.61                # $ fixed
SUPPLY_SALES_TAX_RATE = 0.045         # 4.5%

# --- Delivery components ---
BASIC_SERVICE_CHARGE = 21.28          # $ fixed
DELIVERY_RATE = 0.17192               # $ per kWh
SYSTEM_BENEFIT_CHARGE = 0.00453       # $ per kWh
DELIVERY_GRT_OTHER = 8.60             # $ fixed
DELIVERY_SALES_TAX_RATE = 0.045       # 4.5%

if file:
    df = pd.read_csv(file)

    # --- Rename Date column to 15 Min Interval ---
    if 'Date' in df.columns:
        df.rename(columns={'Date': '15 Min Interval'}, inplace=True)
    
    # Detect usage column
    usage_col = None
    for col in df.columns:
        if "kwh" in col.lower() or "usage" in col.lower():
            usage_col = col
            break

    if not usage_col:
        st.error("Could not find kWh column.")
    else:
        # --- Handle 15-minute interval column ---
        if '15 Min Interval' in df.columns:
            df['DateTime'] = pd.to_datetime(df['15 Min Interval'], errors='coerce')
            df = df.dropna(subset=['DateTime'])
            df['Date'] = df['DateTime'].dt.date

            # Aggregate 15-min readings into daily usage
            daily_usage = df.groupby('Date')[usage_col].sum().reset_index()
            total_days = len(daily_usage)
        else:
            st.warning("No 15 Min Interval column found. Counting rows as days.")
            total_days = len(df)
            daily_usage = df[[usage_col]].copy()
            daily_usage['Date'] = range(1, total_days + 1)

        # --- Calculate Supply Charges ---
        daily_usage['Supply_Charge'] = daily_usage[usage_col] * SUPPLY_RATE
        total_supply = daily_usage['Supply_Charge'].sum()
        total_supply_with_fixed = total_supply + MERCHANT_FUNCTION_CHARGE + SUPPLY_GRT_OTHER
        supply_sales_tax = total_supply_with_fixed * SUPPLY_SALES_TAX_RATE
        total_supply_bill = total_supply_with_fixed + supply_sales_tax

        # --- Calculate Delivery Charges ---
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

        # --- Total Bill ---
        total_kwh = daily_usage[usage_col].sum()
        total_bill = total_supply_bill + total_delivery_bill

        # --- Display Metrics ---
        st.success("File Uploaded and Calculated!")

        st.metric("Total Usage (kWh)", round(total_kwh, 2))
        st.metric("Number of Days Used", total_days)
        st.metric("Supply Charges ($)", f"${round(total_supply_bill, 2)}")
        st.metric("Delivery Charges ($)", f"${round(total_delivery_bill, 2)}")
        st.metric("Estimated Total Bill ($)", f"${round(total_bill, 2)}")

        # Daily usage chart
        st.subheader("📅 Daily Usage (summed from 15-min intervals)")
        st.line_chart(daily_usage.set_index('Date')[usage_col])

        # Raw data
        st.subheader("📄 Daily Aggregated Data")
        st.dataframe(daily_usage)
