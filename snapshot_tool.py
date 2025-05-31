import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

DB_PATH = "evrmore_snapshot.db"

st.set_page_config(page_title="Evrmore Explorer Toolkit", layout="wide")
st.title("🧠 Evrmore Block Explorer Data Science Toolkit")

@st.cache_data
def get_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

@st.cache_data
def query_table(table, limit=1000):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT {limit}", conn)
    conn.close()
    return df

@st.cache_data
def custom_query(sql):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(sql, conn)
    conn.close()
    return df

@st.cache_data
def get_asset_holders(asset_name, block_height):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = """
    SELECT address, SUM(value) as total_balance
    FROM vouts
    WHERE (asset_name = ? OR (? IS NULL AND asset_name IS NULL))
      AND txid IN (
        SELECT txid FROM transactions WHERE block_height <= ?
      )
      AND spent = 0
    GROUP BY address
    ORDER BY total_balance DESC
    """
    cursor.execute(query, (asset_name, asset_name, block_height))
    rows = cursor.fetchall()
    conn.close()
    return pd.DataFrame(rows, columns=["address", "total_balance"])

# Sidebar
st.sidebar.header("🔍 Query Options")
table_list = get_tables()
selected_table = st.sidebar.selectbox("Select a Table", table_list)
custom_sql = st.sidebar.text_area("Or Enter Custom SQL Query")

# Load Data
if custom_sql.strip():
    df = custom_query(custom_sql)
else:
    df = query_table(selected_table)

# Main display
st.subheader(f"📋 Data Preview: {selected_table}")
st.dataframe(df, use_container_width=True)

# Visualization Section
st.subheader("📈 Visualize Data")
with st.expander("Create Chart"):
    if not df.empty:
        columns = df.columns.tolist()
        x_axis = st.selectbox("X Axis", columns)
        y_axis = st.selectbox("Y Axis", columns)
        chart_type = st.selectbox("Chart Type", ["Line", "Bar", "Scatter"])

        if chart_type == "Line":
            fig = px.line(df, x=x_axis, y=y_axis)
        elif chart_type == "Bar":
            fig = px.bar(df, x=x_axis, y=y_axis)
        elif chart_type == "Scatter":
            fig = px.scatter(df, x=x_axis, y=y_axis)

        st.plotly_chart(fig, use_container_width=True)

# Export
st.subheader("⬇️ Export")
st.download_button("Export to CSV", df.to_csv(index=False), f"{selected_table}.csv")

# Snapshot Explorer
st.subheader("📦 Asset Snapshot Explorer")
asset_input = st.text_input("Asset Name (leave blank for EVR)")
block_input = st.number_input("Block Height", min_value=0, value=100)
if st.button("Get Snapshot"):
    asset = asset_input.strip() if asset_input else None
    result_df = get_asset_holders(asset, block_input)
    st.dataframe(result_df)
    st.download_button("Export Snapshot CSV", result_df.to_csv(index=False), f"snapshot_{asset or 'EVR'}_{block_input}.csv")
