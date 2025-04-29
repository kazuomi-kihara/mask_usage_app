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

    # 新規登録フォーム
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

    # 登録済み店舗一覧表示
    st.subheader("登録済み店舗一覧")
    df = get_store_all()
    st.dataframe(df, use_container_width=True)

    # CSVインポート
    st.subheader("CSVインポート（store_id, store_name, area, type）")
    uploaded_file = st.file_uploader("CSVファイルを選択", type="csv", key="store_csv")

    if uploaded_file is not None:
        try:
            df_csv = pd.read_csv(uploaded_file)
            required_cols = {'store_name', 'area', 'type'}
            if required_cols.issubset(df_csv.columns):
                st.dataframe(df_csv)

                if st.button("CSVの内容をDBに登録"):
                    conn = get_connection()
                    for _, row in df_csv.iterrows():
                        conn.execute('INSERT INTO store (store_name, area, type) VALUES (?, ?, ?)', 
                                     (row['store_name'], row['area'], row['type']))
                    conn.commit()
                    conn.close()
                    st.success("CSVデータを登録しました。")
            else:
                st.error("CSVには store_name, area, type の3列が必要です。")
        except Exception as e:
            st.error(f"読み込み中にエラーが発生しました: {e}")

    # 削除機能
    st.subheader("登録済み店舗の削除")
    delete_id = st.number_input("削除したい店舗のIDを入力", min_value=1, step=1)

    if st.button("このIDの店舗を削除"):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM store WHERE id = ?", (delete_id,))
        conn.commit()
        conn.close()
        st.success(f"ID {delete_id} の店舗を削除しました。")
