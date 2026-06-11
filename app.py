# ============================================
# IMPORT LIBRARIES
# ============================================

import streamlit as st
import pandas as pd
import numpy as np
import io  # Added for memory-safe Excel exports

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="Insurance Premium Calculator",
    page_icon="💰",
    layout="wide"
)

# ============================================
# TITLE
# ============================================

st.title("💰 Group Term Life Insurance Premium Calculator")

st.markdown(
    "Upload any insurance Excel file for premium calculation"
)

# ============================================
# SETTINGS
# ============================================

# UPDATED: Changed calculation rate from 320.3 to 767
RATE_PER_LAKH = 767.0

GST_RATE = 0.18

# ============================================
# FILE UPLOAD
# ============================================

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

# ============================================
# PROCESS FILE
# ============================================

if uploaded_file is not None:

    try:

        # ============================================
        # READ FILE
        # ============================================

        df = pd.read_excel(uploaded_file)

        # ============================================
        # CLEAN COLUMN NAMES
        # ============================================

        df.columns = df.columns.str.strip()

        # ============================================
        # SHOW ORIGINAL DATA
        # ============================================

        st.subheader("Uploaded Data")

        st.dataframe(df.head())

        # ============================================
        # HANDLE MISSING COLUMNS
        # ============================================

        required_columns = [
            'Loan Account No.',
            'Name of Primary Loan borrower',
            'Mobile No',
            'Sum Assured'
        ]

        for col in required_columns:
            if col not in df.columns:
                df[col] = ""

        # ============================================
        # CLEAN SUM ASSURED
        # ============================================

        df['Sum Assured'] = pd.to_numeric(
            df['Sum Assured'],
            errors='coerce'
        ).fillna(0)

        # ============================================
        # OPTIONAL AGE COLUMN
        # ============================================

        if 'MAIN MEMBER AGE' not in df.columns:
            df['MAIN MEMBER AGE'] = 0

        # ============================================
        # OPTIONAL LOAN COLUMN
        # ============================================

        if 'Loan Outstanding Amount' not in df.columns:
            df['Loan Outstanding Amount'] = 0

        # ============================================
        # ML RISK SCORE
        # ============================================

        df['Risk Score'] = (
            (df['Sum Assured'] / 100000)
            +
            (pd.to_numeric(
                df['Loan Outstanding Amount'],
                errors='coerce'
            ).fillna(0) / 100000)
        )

        # ============================================
        # ML FEATURES
        # ============================================

        X = df[[
            'Sum Assured',
            'Loan Outstanding Amount'
        ]]

        y = df['Risk Score']

        # ============================================
        # TRAIN TEST SPLIT
        # ============================================

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42
        )

        # ============================================
        # TRAIN MODEL
        # ============================================

        model = RandomForestRegressor(
            random_state=42
        )

        model.fit(
            X_train,
            y_train
        )

        # ============================================
        # PREDICT RISK
        # ============================================

        df['Predicted Risk'] = model.predict(X)

        # ============================================
        # PREMIUM CALCULATION
        # ============================================

        df['Premium Excl GST'] = (
            (df['Sum Assured'] / 100000)
            *
            RATE_PER_LAKH
        )

        # ============================================
        # GST CALCULATION
        # ============================================

        df['Premium + GST'] = (
            df['Premium Excl GST']
            +
            (df['Premium Excl GST'] * GST_RATE)
        )

        # ============================================
        # FINAL OUTPUT
        # ============================================

        output_columns = [
            'Loan Account No.',
            'Name of Primary Loan borrower',
            'Mobile No',
            'MAIN MEMBER AGE',
            'Sum Assured',
            'Predicted Risk',
            'Premium Excl GST',
            'Premium + GST'
        ]

        final_df = df[output_columns]

        # ============================================
        # DASHBOARD
        # ============================================

        st.subheader("Portfolio Summary")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Total Members",
                len(final_df)
            )

        with col2:
            st.metric(
                "Total Sum Assured",
                f"₹ {final_df['Sum Assured'].sum():,.0f}"
            )

        with col3:
            st.metric(
                "Total Premium",
                f"₹ {final_df['Premium + GST'].sum():,.2f}"
            )

        # ============================================
        # SHOW OUTPUT
        # ============================================

        st.subheader("Premium Calculation Output")

        st.dataframe(
            final_df,
            use_container_width=True
        )

        # ============================================
        # DOWNLOAD BUTTON (Memory-Safe Fix)
        # ============================================
        
        # We use BytesIO so multiple app visitors can export files 
        # at the same time without hitting server storage errors.
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            final_df.to_excel(writer, index=False, sheet_name='Premium Summary')
            
        buffer.seek(0)

        st.download_button(
            label="⬇ Download Output Excel",
            data=buffer,
            file_name="Premium_Output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:

        st.error(f"Error: {e}")
