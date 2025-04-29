import streamlit as st
import sqlite3
import pandas as pd

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

def store_page():
    st.title("店舗登録")

    store_name = st.text_input("店舗名を入力")
    area = st.radio("地区を選択", ("延岡地区", "日向地区"))
    store_type = st.radio("種別を選択", ("自店", "競合"))

    if st.button("店舗登録"):
        if store_name:
            conn = get_connection()
            conn.execute('INSERT INTO store (store_name, area, type) VALUES (?, ?, ?)', (store_name, area, store_type))
            conn.commit()
            conn.close()
            st.success("店舗を登録しました！")
        else:
            st.error("店舗名を入力してください。")

    st.subheader("登録済み店舗一覧")
    df = get_store_all()
    st.dataframe(df, use_container_width=True)
