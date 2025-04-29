import streamlit as st
import sqlite3
import pandas as pd

# 店舗名マッピング辞書
STORE_NAME_MAP = {
    #延岡地区
    "西の丸センター": "センター",
    "西の丸延岡店": "延岡店",
    "西の丸古川店": "古川店",
    "サンクス恵比須店": "恵比須",
    "ファミリー三愛延岡店": "ファミリー三愛延岡店",
    "ダイナム宮崎延岡店 ゆったり館": "ダイナム宮崎延岡店 ゆったり館",
    "CORE21南延岡店": "CORE21南延岡店",
    "シリウス延岡店": "シリウス延岡店",
    "オーパス延岡店": "オーパス延岡店",
    "Super D’station39延岡店": "Super D’station39延岡店",

    # 東児湯地区
    "西の丸川南店": "川南",

    # 日向地区
    "西の丸門川店": "門川",
    "西の丸エーワン": "エーワン",
    "CORE21日向店": "CORE21日向店",
    "まるみつ日向店": "まるみつ日向店",
    "ダイナム宮崎日向店 ゆったり館": "ダイナム宮崎日向店 ",
    "ダイナム宮崎日向財光寺店 ゆったり館": "ダイナム宮崎日向財光寺店",
    "シルバーバック日向店": "シルバーバック日向店",
    "Super D’station39日向店": "Super D’station39日向店"
}

DB_FILE = 'mask.db'

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def active_page():
    st.title("稼働データ登録（半自動処理）")

    st.write("### 稼働データメール本文を貼り付けてください：")
    raw_text = st.text_area("メール本文", height=400)

    if st.button("登録処理を開始"):
        if not raw_text.strip():
            st.warning("データが入力されていません。")
            return

        conn = get_connection()
        cursor = conn.cursor()
        lines = raw_text.splitlines()
        current_store = None
        p_val = None
        s_val = None
        result_log = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line in STORE_NAME_MAP:
                current_store = STORE_NAME_MAP[line]
                p_val = None
                s_val = None
                continue

            if current_store:
                if line.startswith("P  計"):
                    try:
                        p_val = int(line.split()[2])
                    except:
                        p_val = None
                elif line.startswith("S  計"):
                    try:
                        s_val = int(line.split()[2])
                    except:
                        s_val = None

                    if p_val is not None and s_val is not None:
                        # DBから該当データ取得
                        cursor.execute("""
                            SELECT ms.id, ms.pachinko_no_mask, ms.slot_no_mask, ms.total_no_mask
                            FROM mask_status ms
                            JOIN store s ON ms.store_id = s.id
                            WHERE s.store_name = ? AND (ms.pachinko_active IS NULL OR ms.pachinko_active = 0)
                            ORDER BY ms.date DESC LIMIT 1
                        """, (current_store,))
                        row = cursor.fetchone()
                        if row:
                            total_active = p_val + s_val
                            p_mask = (
                                (p_val - row["pachinko_no_mask"]) / p_val
                                if p_val > 0 else None
                            )
                            s_mask = (
                                (s_val - row["slot_no_mask"]) / s_val
                                if s_val > 0 else None
                            )
                            t_mask = (
                                (total_active - row["total_no_mask"]) / total_active
                                if total_active > 0 else None
                            )

                            cursor.execute("""
                                UPDATE mask_status
                                SET pachinko_active = ?, slot_active = ?, total_active = ?,
                                    pachinko_mask_rate = ?, slot_mask_rate = ?, total_mask_rate = ?
                                WHERE id = ?
                            """, (p_val, s_val, total_active, p_mask, s_mask, t_mask, row["id"]))
                            result_log.append(f"✅ {current_store} の最新データを更新しました。")
                        else:
                            result_log.append(f"⚠️ {current_store} に該当する未登録データが見つかりませんでした。")

        conn.commit()
        conn.close()

        for msg in result_log:
            st.write(msg)
