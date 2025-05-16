import streamlit as st
import sqlite3
import pandas as pd
from matplotlib import rcParams
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from datetime import datetime
import os
import plotly.express as px  # Plotly追加

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
import active  # 稼働データ登録用ページ
import edit  # データ編集ページ
import comment  # コメント入力ページ
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
    st.title("マスク着用率グラフ")

    # ページ冒頭に追加（mask_rate_page() の最初）
    df_check = get_mask_status_all()
    missing_df = df_check[(df_check['pachinko_active'].isnull()) | (df_check['slot_active'].isnull())]

    if not missing_df.empty:
        missing_stores = missing_df['store_name'].unique()
        msg = "⚠️ 以下の店舗で稼働人数が未入力です：\n\n" + "\n".join(f"- {name}" for name in missing_stores)
        st.warning(msg)


    # --- グラフ表示 ---
    df_all = get_mask_status_all()
    df_all['date'] = pd.to_datetime(df_all['date'])
    df_all['date_label'] = df_all['date'].dt.strftime('%Y年%m月')

    # 最新年月を取得
    latest_date = df_all['date'].max()
    latest_year = latest_date.year
    latest_month = latest_date.month

    # 最新年月のデータを抽出
    df_filtered = df_all[(df_all['year'] == latest_year) & (df_all['month'] == latest_month)]

    if not df_filtered.empty:
        graph_mode = st.radio("グラフ表示方法を選択", ["地区別（平均比較）", "地区別（店舗比較）", "店舗別"])

        if graph_mode == "店舗別":
            store_options = df_all['store_name'].unique()
            selected_store = st.selectbox("店舗を選択してグラフ表示", store_options)
            if selected_store:
                df_store = df_all[df_all['store_name'] == selected_store].copy()
                df_store = df_store.sort_values('date')
                df_store['mask_rate'] = df_store['total_mask_rate'] * 100

                fig = px.line(
                    df_store,
                    x="date_label",
                    y="mask_rate",
                    markers=True,
                    labels={"date_label": "日付", "mask_rate": "着用率（％）"},
                    title=f"{selected_store} のマスク着用率推移"
                )
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)

        elif graph_mode == "地区別（店舗比較）":
            area_options = df_all['area'].dropna().unique()
            selected_area = st.selectbox("地区を選択してグラフ表示", area_options)
            if selected_area:
                df_area = df_all[df_all['area'] == selected_area].copy()
                df_area = df_area.sort_values('date')
                df_area['mask_rate'] = df_area['total_mask_rate'] * 100

                fig = px.line(
                    df_area,
                    x="date_label",
                    y="mask_rate",
                    color="store_name",
                    markers=True,
                    labels={"date_label": "日付", "mask_rate": "着用率（％）", "store_name": "店舗"},
                    title=f"{selected_area} 地区 店舗別マスク着用率推移"
                )
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)

        elif graph_mode == "地区別（平均比較）":
            areas = df_all['area'].dropna().unique()
            plot_data = []

            # --- 全地区（全体平均）を最初に追加 ---
            grouped_all = df_all.groupby('date').agg(
                total_no_mask_sum=('total_no_mask', 'sum'),
                total_active_sum=('total_active', 'sum')
            ).reset_index()
            grouped_all['mask_rate'] = (grouped_all['total_active_sum'] - grouped_all['total_no_mask_sum']) / grouped_all['total_active_sum'] * 100
            grouped_all = grouped_all[grouped_all['total_active_sum'] > 0]
            grouped_all['地区'] = '全地区'
            grouped_all['date_label'] = grouped_all['date'].dt.strftime('%Y年%m月')
            plot_data.append(grouped_all[['date_label', 'mask_rate', '地区']])

            # --- 各地区を追加 ---
            for area in sorted(areas):
                df_area = df_all[df_all['area'] == area].copy()
                grouped = df_area.groupby('date').agg(
                    total_no_mask_sum=('total_no_mask', 'sum'),
                    total_active_sum=('total_active', 'sum')
                ).reset_index()
                grouped['mask_rate'] = (grouped['total_active_sum'] - grouped['total_no_mask_sum']) / grouped['total_active_sum'] * 100
                grouped = grouped[grouped['total_active_sum'] > 0]
                grouped['地区'] = area
                grouped['date_label'] = grouped['date'].dt.strftime('%Y年%m月')
                plot_data.append(grouped[['date_label', 'mask_rate', '地区']])

            # --- データを結合してグラフ化 ---
            df_plot = pd.concat(plot_data)

            fig = px.line(
                df_plot,
                x="date_label",
                y="mask_rate",
                color="地区",
                markers=True,
                labels={"date_label": "日付", "mask_rate": "着用率（％）", "地区": "地区"},
                title="地区別 平均マスク着用率推移"
            )
            fig.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("表示するデータがありません。")

    # マスク着用率 ======
        st.markdown("---")
    st.subheader("マスク着用率一覧（年月指定）")

    # 年月選択
    current_year = datetime.today().year
    current_month = datetime.today().month
    years = list(range(2023, current_year + 2))
    months = [1, 4, 7, 10]

    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("表示する年", years, index=years.index(current_year))
    with col2:
        default_month_index = months.index(current_month) if current_month in months else 0
        selected_month = st.selectbox("表示する月", months, index=default_month_index)

    df_table = df_all[(df_all['year'] == selected_year) & (df_all['month'] == selected_month)].copy()

    if df_table.empty:
        st.info("該当するデータがありません。")
    else:
        df_table_display = df_table[[
            'store_name',
            'pachinko_no_mask', 'slot_no_mask', 'total_no_mask',
            'pachinko_active', 'slot_active', 'total_active',
            'pachinko_mask_rate', 'slot_mask_rate', 'total_mask_rate'
        ]].copy()

        df_table_display.columns = [
            '店舗名', '未着用P', '未着用S', '未着用計',
            '稼働P', '稼働S', '稼働計',
            '着用率P', '着用率S', '着用率計'
        ]

        for col in ['着用率P', '着用率S', '着用率計']:
            df_table_display[col] = df_table_display[col].apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "")

        st.dataframe(
            df_table_display,
            use_container_width=True,
            column_order=["店舗名"] + [col for col in df_table_display.columns if col != "店舗名"],
            column_config={
                "店舗名": st.column_config.TextColumn("店舗名", pinned="left")
            }
        )

    # ===== コメント表示 =====
    st.subheader("コメント一覧")

    # DBからコメントを取得
    conn = get_connection()
    comments_df = pd.read_sql_query('''
        SELECT year, month, comment, created_at
        FROM comments
        ORDER BY year DESC, month DESC, created_at DESC
    ''', conn)
    conn.close()

    comments_df_display = comments_df[['year', 'month', 'comment']].copy()
    comments_df_display.columns = ['年', '月', 'コメント']  # ← 列名を短く
    comments_df_display['年'] = comments_df_display['年'].astype(str)  # ← 文字列に変換
    comments_df_display['月'] = comments_df_display['月'].astype(str)  # ← 文字列に変換

    st.dataframe(comments_df_display, use_container_width=True)


# ===== ページ切り替え =====
st.set_page_config(page_title="マスク管理システム", layout="wide")

page = st.sidebar.selectbox("ページを選択", ("マスク着用率一覧", "非着用者入力", "店舗登録", "稼働データ登録", "データ修正", "コメント入力"))

if page == "マスク着用率一覧":
    mask_rate_page()
elif page == "非着用者入力":
    mask.mask_page()
elif page == "店舗登録":
    store.store_page()
elif page == "稼働データ登録":
    active.active_page()
elif page == "データ修正":
    edit.edit_page()
elif page == "コメント入力":
    comment.comment_page()
