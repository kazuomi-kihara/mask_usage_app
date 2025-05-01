import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import numpy as np

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

    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y/%m/%d')
    selected_date = st.selectbox("日付を選択", df['date'])
    row = df[df['date'] == selected_date].iloc[0].to_dict()

    st.subheader(f"{selected_date} のデータ修正")

    new_values = {}

    for column in ['pachinko_no_mask', 'slot_no_mask', 'pachinko_active', 'slot_active']:
        default_val = float(row[column]) if pd.notnull(row[column]) else 0
        new_values[column] = st.number_input(
            column.replace('_', ' ').title(), value=default_val, step=1.0, format="%f"
        )

    new_values['total_no_mask'] = new_values['pachinko_no_mask'] + new_values['slot_no_mask']
    new_values['total_active'] = new_values['pachinko_active'] + new_values['slot_active']

    def calc_rate(active, no_mask):
        return round((active - no_mask) / active, 4) if active > 0 else None

    new_values['pachinko_mask_rate'] = calc_rate(new_values['pachinko_active'], new_values['pachinko_no_mask'])
    new_values['slot_mask_rate'] = calc_rate(new_values['slot_active'], new_values['slot_no_mask'])
    new_values['total_mask_rate'] = calc_rate(new_values['total_active'], new_values['total_no_mask'])

    if st.button("更新する"):
        current_data = pd.read_sql_query("SELECT * FROM mask_status WHERE id = ?", conn, params=(row['id'],)).iloc[0].to_dict()

        # 値の違いをチェック
        has_changes = False
        for k in new_values:
            if isinstance(new_values[k], float) and isinstance(current_data[k], float):
                if not np.isclose(new_values[k], current_data[k], rtol=1e-04):
                    has_changes = True
                    break
            elif new_values[k] != current_data[k]:
                has_changes = True
                break

        if has_changes:
            cursor = conn.execute(
                """
                UPDATE mask_status
                SET
                    pachinko_no_mask = ?, slot_no_mask = ?, total_no_mask = ?,
                    pachinko_active = ?, slot_active = ?, total_active = ?,
                    pachinko_mask_rate = ?, slot_mask_rate = ?, total_mask_rate = ?
                WHERE id = ?
                """,
                (
                    new_values['pachinko_no_mask'], new_values['slot_no_mask'], new_values['total_no_mask'],
                    new_values['pachinko_active'], new_values['slot_active'], new_values['total_active'],
                    new_values['pachinko_mask_rate'], new_values['slot_mask_rate'], new_values['total_mask_rate'],
                    row['id']
                )
            )
            conn.commit()
            st.success("データを更新しました。")
            st.write(f"更新対象ID: {row['id']}")
            st.write(f"変更件数: {cursor.rowcount} 件")
        else:
            st.info("変更が検出されなかったため、更新は行われませんでした。")

    conn.close()
