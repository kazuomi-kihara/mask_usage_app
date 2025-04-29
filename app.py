import streamlit as st
import sqlite3
import pandas as pd
from matplotlib import rcParams
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from datetime import datetime
import os
import plotly.express as px

# --- フォントパスの設定 ---
font_path = os.path.join(os.path.dirname(__file__), "fonts", "ipaexg.ttf")
if os.path.exists(font_path):
    font_prop = FontProperties(fname=font_path)
    rcParams['font.family'] = font_prop.get_name()
else:
    print("フォントが見つかりません:", font_path)

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
    months = [1, 4, 7, 10]  # 四半期のみ

    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("西暦を選択", years, index=years.index(current_year))
    with col2:
        selected_month = st.selectbox("月を選択", months, index=months.index(current_month) if current_month in months else 0)

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

        graph_mode = st.radio("グラフ表示方法を選択", ["店舗別", "地区別（店舗比較）", "地区別（平均比較）"])
        df_all = get_mask_status_all()
        df_all['date'] = pd.to_datetime(df_all['date'])

        if graph_mode == "店舗別":
            store_options = df_filtered['store_name'].unique()
            selected_store = st.selectbox("店舗を選択してグラフ表示", store_options)
            if selected_store:
                df_store = df_all[df_all['store_name'] == selected_store].copy()
                df_store = df_store.sort_values('date')

                fig, ax = plt.subplots(figsize=(8, 4))
                ax.plot(df_store['date'], df_store['total_mask_rate'] * 100, marker='o')
                ax.set_ylim(0, 100)
                ax.set_title(f"{selected_store} のマスク着用率推移", fontproperties=font_prop)
                ax.set_xlabel("日付", fontproperties=font_prop)
                ax.set_ylabel("着用率（％）", fontproperties=font_prop)
                ax.grid(True)
                plt.xticks(rotation=45)
                st.pyplot(fig)

        elif graph_mode == "地区別（店舗比較）":
            area_options = df_filtered['area'].unique()
            selected_area = st.selectbox("地区を選択してグラフ表示", area_options)
            if selected_area:
                df_area = df_all[df_all['area'] == selected_area].copy()
                df_area = df_area.sort_values('date')

                fig, ax = plt.subplots(figsize=(8, 4))
                for store_name, group in df_area.groupby('store_name'):
                    ax.plot(group['date'], group['total_mask_rate'] * 100, marker='o', label=store_name)
                ax.set_ylim(0, 100)
                ax.set_title(f"{selected_area} のマスク着用率推移", fontproperties=font_prop)
                ax.set_xlabel("日付", fontproperties=font_prop)
                ax.set_ylabel("着用率（％）", fontproperties=font_prop)
                ax.grid(True)
                ax.legend(prop=font_prop, fontsize=6, loc='upper left', bbox_to_anchor=(1, 1))
                plt.xticks(rotation=45)
                st.pyplot(fig)

        elif graph_mode == "地区別（平均比較）":
            df_all = get_mask_status_all()
            df_all['date'] = pd.to_datetime(df_all['date'], errors='coerce')
            df_all = df_all[df_all['date'].notnull()]

            areas = ['延岡地区', '日向地区', '東児湯地区']
            plot_data = []

            for area in areas:
                df_area = df_all[df_all['area'] == area].copy()
                grouped = df_area.groupby('date').agg(
                    total_no_mask_sum=('total_no_mask', 'sum'),
                    total_active_sum=('total_active', 'sum')
                ).reset_index()

                grouped['mask_rate'] = (grouped['total_active_sum'] - grouped['total_no_mask_sum']) / grouped['total_active_sum'] * 100
                grouped = grouped[grouped['total_active_sum'] > 0]

                grouped['地区'] = area
                plot_data.append(grouped[['date', 'mask_rate', '地区']])

            # --- 県北地区（全体）を追加 ---
            grouped_all = df_all.groupby('date').agg(
                total_no_mask_sum=('total_no_mask', 'sum'),
                total_active_sum=('total_active', 'sum')
            ).reset_index()

            grouped_all['mask_rate'] = (grouped_all['total_active_sum'] - grouped_all['total_no_mask_sum']) / grouped_all['total_active_sum'] * 100
            grouped_all = grouped_all[grouped_all['total_active_sum'] > 0]
            grouped_all['地区'] = '県北地区'

            plot_data.append(grouped_all[['date', 'mask_rate', '地区']])

            # 全地区まとめて
            df_plot = pd.concat(plot_data)
            
            # Plotlyでグラフ描画
            fig = px.line(
                df_plot,
                x='date',
                y='mask_rate',
                color='地区',
                markers=True,
                labels={"date": "日付", "mask_rate": "着用率（％）", "地区": "地区"},
                title="地区別 平均マスク着用率推移"
            )
            fig.update_layout(yaxis_range=[0, 100])

            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("表示するデータがありません。")

# ===== ページ切り替え =====
st.set_page_config(page_title="マスク管理システム", layout="wide")

page = st.sidebar.selectbox("ページを選択", ("マスク着用率一覧", "非着用者入力","店舗登録" ))

if page == "マスク着用率一覧":
    mask_rate_page()
elif page == "非着用者入力":
    mask.mask_page()
elif page == "店舗登録":
    store.store_page()

