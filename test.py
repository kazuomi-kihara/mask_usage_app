import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# タイトル
st.title("簡単な表示テスト")

# データ読み込み（例：CSVが同じフォルダにある場合）
uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.subheader("📊 アップロードしたデータ")
    st.dataframe(df)

    # 数値列を選ばせる
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if numeric_cols:
        col = st.selectbox("グラフにする列を選んでください", numeric_cols)

        # グラフ表示
        fig, ax = plt.subplots()
        df[col].plot(kind='line', ax=ax)
        st.pyplot(fig)
    else:
        st.warning("数値データが見つかりませんでした")
else:
    st.info("CSVファイルをアップロードしてください")
