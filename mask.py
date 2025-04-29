import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ===== DB接続 =====
DB_FILE = 'mask.db'

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_store_all():
    conn = get_connection()
    df = pd.read_sql_query('SELECT * FROM store ORDER BY id', conn)
    conn.close()
    return df

def get_mask_status_all():
    conn = get_connection()
    df = pd.read_sql_query('''
        SELECT ms.id, s.store_name, ms.date, ms.year, ms.month,
               ms.pachinko_no_mask, ms.slot_no_mask, ms.total_no_mask,
               ms.pachinko_active, ms.slot_active, ms.total_active,
               ms.pachinko_mask_rate, ms.slot_mask_rate, ms.total_mask_rate
        FROM mask_status ms
        JOIN store s ON ms.store_id = s.id
        ORDER BY ms.date DESC, ms.store_id
    ''', conn)
    conn.close()
    return df

def mask_page():
    st.title("非着用者＋稼働人数入力")

    # ----- 入力フォーム -----
    stores = get_store_all()
    store_name_to_id = {row['store_name']: row['id'] for _, row in stores.iterrows()}
    store_selection = st.selectbox("店舗を選択", list(store_name_to_id.keys()))
    selected_date = st.date_input("日付を選択", datetime.today())

    pachinko_no_mask = st.number_input("非着用人数（パチンコ）", min_value=0, step=1)
    slot_no_mask = st.number_input("非着用人数（スロット）", min_value=0, step=1)
    pachinko_active = st.number_input("稼働人数（パチンコ）", min_value=0, step=1, value=0)
    slot_active = st.number_input("稼働人数（スロット）", min_value=0, step=1, value=0)

    if st.button("データ登録"):
        year = selected_date.year
        month = selected_date.month
        total_no_mask = pachinko_no_mask + slot_no_mask

        pachinko_mask_rate = round((pachinko_active - pachinko_no_mask) / pachinko_active * 100) if pachinko_active else None
        slot_mask_rate = round((slot_active - slot_no_mask) / slot_active * 100) if slot_active else None
        total_active = pachinko_active + slot_active if pachinko_active and slot_active else None
        total_mask_rate = round((total_active - total_no_mask) / total_active * 100) if total_active else None

        conn = get_connection()
        conn.execute('''
            INSERT INTO mask_status (
                store_id, date, year, month,
                pachinko_no_mask, slot_no_mask, total_no_mask,
                pachinko_active, slot_active, total_active,
                pachinko_mask_rate, slot_mask_rate, total_mask_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (store_name_to_id[store_selection], selected_date.strftime("%Y/%m/%d"), year, month,
              pachinko_no_mask, slot_no_mask, total_no_mask,
              pachinko_active or None, slot_active or None, total_active,
              pachinko_mask_rate, slot_mask_rate, total_mask_rate))
        conn.commit()
        conn.close()
        st.success("データを登録しました！")

    # ----- CSVインポート -----
    st.subheader("CSV一括インポート")
    uploaded_file = st.file_uploader("CSVファイルをアップロード", type="csv", key="mask_upload")

    if uploaded_file is not None:
        try:
            df_upload = pd.read_csv(uploaded_file)

            required_columns = [
                'store_id', 'date', 'year', 'month',
                'pachinko_no_mask', 'slot_no_mask', 'total_no_mask',
                'pachinko_active', 'slot_active', 'total_active',
                'pachinko_mask_rate', 'slot_mask_rate', 'total_mask_rate'
            ]

            if set(required_columns).issubset(df_upload.columns):
                st.dataframe(df_upload, use_container_width=True)

                if st.button("アップロードデータをDBに登録"):
                    conn = get_connection()
                    for _, row in df_upload.iterrows():
                        conn.execute('''
                            INSERT INTO mask_status (
                                store_id, date, year, month,
                                pachinko_no_mask, slot_no_mask, total_no_mask,
                                pachinko_active, slot_active, total_active,
                                pachinko_mask_rate, slot_mask_rate, total_mask_rate
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            row['store_id'], row['date'], row['year'], row['month'],
                            row['pachinko_no_mask'], row['slot_no_mask'], row['total_no_mask'],
                            row['pachinko_active'], row['slot_active'], row['total_active'],
                            row['pachinko_mask_rate'], row['slot_mask_rate'], row['total_mask_rate']
                        ))
                    conn.commit()
                    conn.close()
                    st.success("CSVデータをDBに登録しました！")
            else:
                st.error("CSVに必要なカラムがすべて含まれていません。")

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

    # ----- 登録済みデータ一覧表示 -----
    st.subheader("登録済みデータ一覧")
    df_mask = get_mask_status_all()
    st.dataframe(df_mask, use_container_width=True)

    # ----- 削除機能 -----
    st.subheader("登録データの削除")
    delete_id = st.number_input("削除したいデータのIDを入力", min_value=1, step=1)

    if st.button("このIDのデータを削除"):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM mask_status WHERE id = ?", (delete_id,))
        conn.commit()
        conn.close()
        st.success(f"ID {delete_id} のデータを削除しました。")
