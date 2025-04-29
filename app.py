import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# ===== サブページ読み込み =====
import store
import mask

# ===== DB接続 =====
DB_FILE = 'mask.db'

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_mask_status_all():
    conn = get_connection()
    df = pd.read_sql_query('''
        SELECT ms.id, s.store_name, ms.date, ms.year, ms.month,
               ms.pachinko_no_mask, ms.slot_no_mask, ms.total_no_mask,
               ms.pachinko_active, ms.slot_active, ms.total_active,
               ms.pachinko_mask_rate, ms.slot_mask_rate, ms.total_mask_rate,
               s.area, s.type
        FROM mask_status ms
        JOIN store s ON ms.store_id = s.id
        ORDER BY ms.date DESC, ms.store_id
    ''', conn)
    conn.close()
    return df

def mask_rate_page():
    st.title("マスク着用率一覧")

    # ===== 年月選択 =====
    current_year = datetime.today().year
    current_month = datetime.today().month
    years = list(range(2023, current_year + 2))
    months = list(range(1, 13))

    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("西暦を選択", years, index=years.index(current_year))
    with col2:
        selected_month = st.selectbox("月を選択", months, index=current_month - 1)

    if st.button("表示する") or 'df_filtered' in st.session_state:
        df = get_mask_status_all()
        df_filtered = df[(df['year'] == selected_year) & (df['month'] == selected_month)]
        st.session_state['df_filtered'] = df_filtered
    else:
        df_filtered = pd.DataFrame()

    if not df_filtered.empty:
        df_display = df_filtered[[
            'store_name',
            'pachinko_no_mask', 'slot_no_mask', 'total_no_mask',
            'pachinko_active', 'slot_active', 'total_active',
            'pachinko_mask_rate', 'slot_mask_rate', 'total_mask_rate']].copy()

        df_display.columns = [
            '店舗名', '未着用P', '未着用S', '未着用計',
            '稼働P', '稼働S', '稼働計',
            '着用率P', '着用率S', '着用率計']

        df_display['着用率P'] = df_display['着用率P'].apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "")
        df_display['着用率S'] = df_display['着用率S'].apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "")
        df_display['着用率計'] = df_display['着用率計'].apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "")

        st.dataframe(df_display, use_container_width=True)

        # 店舗選択とグラフ表示
        store_options = df_filtered['store_name'].unique()
        selected_store = st.selectbox("店舗を選択してグラフ表示", store_options)

        if selected_store:
            df_all = get_mask_status_all()
            df_store = df_all[df_all['store_name'] == selected_store].copy()
            df_store['date'] = pd.to_datetime(df_store['date'])
            df_store = df_store.sort_values('date')

            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(df_store['date'], df_store['total_mask_rate'] * 100, marker='o')
            ax.set_ylim(0, 100)
            ax.set_title(f"{selected_store} のマスク着用率推移")
            ax.set_xlabel("日付")
            ax.set_ylabel("着用率（％）")
            ax.grid(True)
            plt.xticks(rotation=45)
            st.pyplot(fig)
    else:
        st.info("表示するデータがありません。")

# ===== ページ切り替え =====
st.set_page_config(page_title="マスク管理システム", layout="wide")

page = st.sidebar.selectbox("ページを選択", ("店舗登録", "非着用者入力", "マスク着用率一覧"))

if page == "店舗登録":
    store.store_page()
elif page == "非着用者入力":
    mask.mask_page()
elif page == "マスク着用率一覧":
    mask_rate_page()
