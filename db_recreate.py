import sqlite3

# ===== データベースファイルのパス =====
DB_FILE = 'mask.db'  # 必要に応じてここを変更

# ===== データベース接続 =====
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# ===== 既存の mask_status テーブルを削除（もし存在すれば） =====
cursor.execute('DROP TABLE IF EXISTS mask_status')

# ===== mask_status テーブルを新規作成 =====
cursor.execute('''
    CREATE TABLE mask_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        pachinko_no_mask INTEGER NOT NULL,
        slot_no_mask INTEGER NOT NULL,
        total_no_mask INTEGER NOT NULL,
        pachinko_active INTEGER,
        slot_active INTEGER,
        total_active INTEGER,
        pachinko_mask_rate REAL,
        slot_mask_rate REAL,
        total_mask_rate REAL,
        FOREIGN KEY (store_id) REFERENCES store (id)
    )
''')

# ===== コミット＆クローズ =====
conn.commit()
conn.close()

print("新しい mask_status テーブルを作成しました。")
