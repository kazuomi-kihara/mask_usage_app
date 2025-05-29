import streamlit as st
import sqlite3

DB_FILE = "mask.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def config_page():
    st.title("グラフ表示設定")

    conn = get_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value REAL
        )
    ''')

    # 現在値取得
    cur = conn.execute("SELECT key, value FROM config WHERE key IN ('y_min', 'y_max')")
    config_dict = {row['key']: row['value'] for row in cur.fetchall()}

    y_min = st.number_input("Y軸の下限（％）", value=config_dict.get("y_min", 0), step=1.0)
    y_max = st.number_input("Y軸の上限（％）", value=config_dict.get("y_max", 100), step=1.0)

    if st.button("保存"):
        conn.execute("REPLACE INTO config (key, value) VALUES ('y_min', ?)", (y_min,))
        conn.execute("REPLACE INTO config (key, value) VALUES ('y_max', ?)", (y_max,))
        conn.commit()
        st.success("設定を保存しました")

    conn.close()

def get_graph_y_range():
    st.sidebar.markdown("### グラフ設定")
    y_min = st.sidebar.number_input("Y軸最小値", min_value=0, max_value=100, value=0, step=1)
    y_max = st.sidebar.number_input("Y軸最大値", min_value=0, max_value=100, value=100, step=1)
    return y_min, y_max