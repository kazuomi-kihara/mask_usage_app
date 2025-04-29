import sqlite3

# ===== データベースファイルのパス =====
DB_FILE = 'mask.db'

# ===== データベース接続 =====
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# ===== storeテーブル削除（もし存在すれば） =====
cursor.execute('DROP TABLE IF EXISTS store')

# ===== 新storeテーブル作成 =====
cursor.execute('''
    CREATE TABLE store (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_name TEXT NOT NULL,
        area TEXT NOT NULL,
        type TEXT NOT NULL
    )
''')

# ===== 保存・クローズ =====
conn.commit()
conn.close()
