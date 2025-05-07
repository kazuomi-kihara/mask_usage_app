import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB_FILE = 'mask.db'

# ===== DB接続 =====
def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ===== コメント表示・操作ページ =====
def comment_page():
    st.title("コメント管理ページ")

    conn = get_connection()
    cur = conn.cursor()

    # ===== テーブルがなければ作成 =====
    cur.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            month INTEGER,
            comment TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()

    # ===== 新規登録 or 修正の切り替え =====
    mode = st.radio("操作を選択", ("新規登録", "修正"))

    if mode == "新規登録":
        st.subheader("新しいコメントを登録")
        new_comment = st.text_area("コメントを入力", height=150)

        if st.button("登録する"):
            today = datetime.today()
            year = today.year
            month = today.month
            created_at = today.strftime('%Y-%m-%d %H:%M:%S')

            conn.execute("INSERT INTO comments (year, month, comment, created_at) VALUES (?, ?, ?, ?)",
                         (year, month, new_comment, created_at))
            conn.commit()
            st.success("コメントを登録しました")

    elif mode == "修正":
        st.subheader("既存コメントの修正")
        df = pd.read_sql_query("SELECT * FROM comments ORDER BY created_at DESC", conn)

        if df.empty:
            st.info("コメントが登録されていません")
        else:
            df['表示'] = df['year'].astype(str) + "年" + df['month'].astype(str) + "月：" + df['comment'].str.slice(0, 20)
            selected_row = st.selectbox("修正するコメントを選択", df['表示'])
            selected_id = df.loc[df['表示'] == selected_row, 'id'].values[0]
            selected_comment = df.loc[df['id'] == selected_id, 'comment'].values[0]

            edited_comment = st.text_area("コメントを修正", value=selected_comment, height=150)

            if st.button("更新する"):
                conn.execute("UPDATE comments SET comment = ? WHERE id = ?", (edited_comment, selected_id))
                conn.commit()
                st.success("コメントを更新しました")

    # ===== 表示一覧 =====
    st.subheader("コメント一覧")
    df = pd.read_sql_query("SELECT year, month, comment FROM comments ORDER BY created_at DESC", conn)

    if df.empty:
        st.info("登録されたコメントはありません")
    else:
        df.columns = ["西暦", "月", "コメント"]
        st.dataframe(df, use_container_width=True)

    conn.close()
