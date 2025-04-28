import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta
import random

# --- DB準備 ---
conn = sqlite3.connect('mask.db')
c = conn.cursor()

# --- 店舗テーブル ---
c.execute('''
    CREATE TABLE IF NOT EXISTS store (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_name TEXT NOT NULL UNIQUE,
        location TEXT
    )
''')

# --- mask_status テーブル ---
c.execute('''
    CREATE TABLE IF NOT EXISTS mask_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        pachinko_no_mask INTEGER NOT NULL,
        slot_no_mask INTEGER NOT NULL,
        total_no_mask INTEGER NOT NULL,
        FOREIGN KEY (store_id) REFERENCES store (id)
    )
''')
conn.commit()

# --- 過去データ（1回だけ投入） ---
c.execute('SELECT COUNT(*) FROM mask_status')
count = c.fetchone()[0]
if count == 0:
    stores = pd.read_sql_query('SELECT id FROM store', conn)
    today = date.today()
    for store_id in stores['id']:
        for i in range(10):  # 10日分
            day = today - timedelta(days=i)
            pachinko = random.randint(0, 5)
            slot = random.randint(0, 5)
            total = pachinko + slot
            year = day.year
            month = day.month
            c.execute('''
                INSERT INTO mask_status 
                (store_id, date, year, month, pachinko_no_mask, slot_no_mask, total_no_mask)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (store_id, day.strftime('%Y-%m-%d'), year, month, pachinko, slot, total))
    conn.commit()

# --- ページ選択 ---
st.sidebar.title('メニュー')
page = st.sidebar.radio('ページを選んでください', ('店舗登録', '非着用者入力', '過去推移グラフ'))

# --- 店舗登録ページ ---
if page == '店舗登録':
    st.title('店舗登録')
    with st.form(key='store_form'):
        store_name = st.text_input('店舗名')
        location = st.text_input('場所（任意）')
        submit_button = st.form_submit_button('登録')
        if submit_button:
            try:
                c.execute('INSERT INTO store (store_name, location) VALUES (?, ?)',
                          (store_name, location))
                conn.commit()
                st.success(f'店舗「{store_name}」を登録しました！')
            except sqlite3.IntegrityError:
                st.error('その店舗名はすでに登録されています。')

    # 登録済み店舗一覧
    st.header('登録済み店舗一覧')
    df_store = pd.read_sql_query('SELECT * FROM store', conn)
    st.dataframe(df_store)

# --- 非着用者入力ページ ---
elif page == '非着用者入力':
    st.title('非着用者数の入力（過去データもOK）')

    stores = pd.read_sql_query('SELECT id, store_name FROM store', conn)
    store_options = dict(zip(stores['store_name'], stores['id']))

    if store_options:
        selected_store = st.selectbox('店舗を選択', list(store_options.keys()))
        selected_date = st.date_input('日付を選択（過去でもOK）', date.today())  # ← ここが修正ポイント！
        pachinko_count = st.number_input('非着用者人数（パチンコ）', min_value=0, step=1)
        slot_count = st.number_input('非着用者人数（スロット）', min_value=0, step=1)
        submit_mask = st.button('登録')

        if submit_mask:
            store_id = store_options[selected_store]
            total_count = pachinko_count + slot_count
            year = selected_date.year
            month = selected_date.month
            c.execute('SELECT id FROM mask_status WHERE store_id = ? AND date = ?', 
                      (store_id, selected_date.strftime('%Y-%m-%d')))
            exists = c.fetchone()
            if exists:
                c.execute('''
                    UPDATE mask_status 
                    SET pachinko_no_mask = ?, slot_no_mask = ?, total_no_mask = ?, year = ?, month = ?
                    WHERE store_id = ? AND date = ?
                ''', (pachinko_count, slot_count, total_count, year, month, store_id, selected_date.strftime('%Y-%m-%d')))
                st.info('既存データを更新しました。')
            else:
                c.execute('''
                    INSERT INTO mask_status 
                    (store_id, date, year, month, pachinko_no_mask, slot_no_mask, total_no_mask)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (store_id, selected_date.strftime('%Y-%m-%d'), year, month, pachinko_count, slot_count, total_count))
                st.success('非着用者人数を登録しました！')
            conn.commit()
    else:
        st.warning('まず店舗を登録してください。')

    # 入力済みデータ一覧
    st.header('非着用者データ一覧')
    query = '''
        SELECT ms.id, s.store_name, ms.date, ms.year, ms.month, 
               ms.pachinko_no_mask, ms.slot_no_mask, ms.total_no_mask
        FROM mask_status ms
        JOIN store s ON ms.store_id = s.id
        ORDER BY ms.date DESC
    '''
    df_mask = pd.read_sql_query(query, conn)
    st.dataframe(df_mask)


# --- 過去推移グラフページ ---
elif page == '過去推移グラフ':
    st.title('店舗別 非着用者数の推移グラフ')

    stores = pd.read_sql_query('SELECT id, store_name FROM store', conn)
    st.header('店舗を選んで過去の非着用者推移を見る')

    cols = st.columns(len(stores))

    for idx, row in stores.iterrows():
        if cols[idx].button(row['store_name']):
            query = '''
                SELECT date, pachinko_no_mask, slot_no_mask, total_no_mask
                FROM mask_status
                WHERE store_id = ?
                ORDER BY date
            '''
            df_mask = pd.read_sql_query(query, conn, params=(row['id'],))
            st.subheader(f'店舗：{row["store_name"]} の非着用者推移')
            st.line_chart(df_mask.set_index('date')[['pachinko_no_mask', 'slot_no_mask', 'total_no_mask']])

conn.close()
