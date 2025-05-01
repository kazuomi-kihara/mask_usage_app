import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB_FILE = 'mask.db'

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def edit_page():
    st.title("データ修正ページ")

    conn = get_connection()
    stores = pd.read_sql_query("SELECT id, store_name FROM store ORDER BY store_name", conn)
    store_dict = dict(zip(stores['store_name'], stores['id']))

    selected_store = st.selectbox("店舗を選択", stores['store_name'])
    store_id = store_dict[selected_store]

    df = pd.read_sql_query(
        "SELECT * FROM mask_status WHERE store_id = ? ORDER BY date DESC",
        conn, params=(store_id,)
    )

    if df.empty:
        st.info("この店舗のデータが見つかりません。")
        return

    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    selected_date = st.selectbox("日付を選択", df['date'])
    row = df[df['date'] == selected_date].iloc[0]

    st.subheader(f"{selected_date} のデータ修正")
    pachinko_no_mask = st.number_input("未着用P", value=row['pachinko_no_mask'], step=1)
    slot_no_mask = st.number_input("未着用S", value=row['slot_no_mask'], step=1)
    total_no_mask = pachinko_no_mask + slot_no_mask

    pachinko_active = st.number_input("稼働P", value=row['pachinko_active'], step=1)
    slot_active = st.number_input("稼働S", value=row['slot_active'], step=1)
    total_active = pachinko_active + slot_active

    # 着用率の自動計算
    pachinko_mask_rate = (pachinko_active - pachinko_no_mask) / pachinko_active if pachinko_active > 0 else None
    slot_mask_rate = (slot_active - slot_no_mask) / slot_active if slot_active > 0 else None
    total_mask_rate = (total_active - total_no_mask) / total_active if total_active > 0 else None

    if st.button("更新する"):
        conn.execute(
            """
            UPDATE mask_status
            SET
                pachinko_no_mask = ?, slot_no_mask = ?, total_no_mask = ?,
                pachinko_active = ?, slot_active = ?, total_active = ?,
                pachinko_mask_rate = ?, slot_mask_rate = ?, total_mask_rate = ?
            WHERE id = ?
            """,
            (
                pachinko_no_mask, slot_no_mask, total_no_mask,
                pachinko_active, slot_active, total_active,
                pachinko_mask_rate, slot_mask_rate, total_mask_rate,
                row['id']
            )
        )
        conn.commit()
        st.success("データを更新しました。")

    conn.close()
