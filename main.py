import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ------------------------------------------------------
# 기본 설정
# ------------------------------------------------------
st.set_page_config(
    page_title="서울 100년 기온 변화",
    page_icon="🌡️",
    layout="centered"
)

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df = df.dropna(subset=["날짜", "평균기온"])
    df["연도"] = df["날짜"].dt.year
    return df


@st.cache_data
def get_yearly_mean(df):
    yearly = (
        df.groupby("연도")
        .agg(
            연평균기온=("평균기온", "mean"),
            일수=("평균기온", "count"),
        )
        .reset_index()
    )
    # 관측일수가 너무 적은 해(연도 시작/끝 부분)는 제외해서 그래프를 더 정확하게
    yearly = yearly[yearly["일수"] >= 300].reset_index(drop=True)
    return yearly


# ------------------------------------------------------
# 데이터 불러오기
# ------------------------------------------------------
with st.spinner("서울 기온 데이터를 불러오는 중입니다..."):
    raw_df = load_data()
    yearly_df = get_yearly_mean(raw_df)

# ------------------------------------------------------
# 헤더
# ------------------------------------------------------
st.title("🌡️ 서울, 100년의 기온 변화")
st.markdown(
    """
지난 100여 년간 서울의 **연평균 기온**이 어떻게 변해왔는지 한눈에 살펴보는 그래프입니다.  
데이터 출처: [서울 기상 데이터 (기상청)](https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv)
"""
)

start_year = int(yearly_df["연도"].min())
end_year = int(yearly_df["연도"].max())
first_temp = yearly_df.iloc[0]["연평균기온"]
last_temp = yearly_df.iloc[-1]["연평균기온"]
temp_diff = last_temp - first_temp

# ------------------------------------------------------
# 요약 지표
# ------------------------------------------------------
col1, col2, col3 = st.columns(3)
col1.metric("관측 기간", f"{start_year} ~ {end_year}년")
col2.metric(f"{start_year}년 연평균 기온", f"{first_temp:.1f} ℃")
col3.metric(f"{end_year}년 연평균 기온", f"{last_temp:.1f} ℃", delta=f"{temp_diff:+.1f} ℃")

st.divider()

# ------------------------------------------------------
# 그래프
# ------------------------------------------------------
st.subheader("📈 연평균 기온 변화 그래프")

# 추세선 계산 (선형 회귀)
x = yearly_df["연도"].values
y = yearly_df["연평균기온"].values
coeffs = np.polyfit(x, y, 1)
trend = np.polyval(coeffs, x)
기온_상승_기울기 = coeffs[0]

# 5년 이동평균
yearly_df["5년_이동평균"] = yearly_df["연평균기온"].rolling(window=5, center=True).mean()

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=yearly_df["연도"],
    y=yearly_df["연평균기온"],
    mode="lines+markers",
    name="연평균 기온",
    line=dict(color="#90A4AE", width=1.5),
    marker=dict(size=4),
    hovertemplate="%{x}년<br>연평균 기온: %{y:.1f}℃<extra></extra>",
))

fig.add_trace(go.Scatter(
    x=yearly_df["연도"],
    y=yearly_df["5년_이동평균"],
    mode="lines",
    name="5년 이동평균",
    line=dict(color="#1E88E5", width=3),
    hovertemplate="%{x}년<br>5년 이동평균: %{y:.1f}℃<extra></extra>",
))

fig.add_trace(go.Scatter(
    x=yearly_df["연도"],
    y=trend,
    mode="lines",
    name="전체 추세선",
    line=dict(color="#E53935", width=2, dash="dash"),
    hovertemplate="%{x}년<br>추세선: %{y:.1f}℃<extra></extra>",
))

fig.update_layout(
    xaxis_title="연도",
    yaxis_title="연평균 기온 (℃)",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=10, r=10, t=40, b=10),
    height=500,
)

st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------
# 해석 문구
# ------------------------------------------------------
st.subheader("🔍 그래프 해석")
연간_상승폭_100년 = 기온_상승_기울기 * 100

if 기온_상승_기울기 > 0:
    방향 = "상승"
else:
    방향 = "하락"

st.markdown(
    f"""
- 회색 선은 **매년의 연평균 기온**, 파란 선은 변동을 부드럽게 보여주는 **5년 이동평균**입니다.
- 빨간 점선은 전체 기간의 **추세선**으로, 서울의 연평균 기온은 약 **100년당 {연간_상승폭_100년:+.1f}℃** {방향}하는 추세를 보입니다.
- {start_year}년 연평균 기온은 **{first_temp:.1f}℃**였지만, {end_year}년에는 **{last_temp:.1f}℃**로 변화했습니다.
"""
)

# ------------------------------------------------------
# 원본 데이터 보기 (선택)
# ------------------------------------------------------
with st.expander("📋 연도별 평균 기온 표 보기"):
    st.dataframe(
        yearly_df[["연도", "연평균기온", "5년_이동평균"]].rename(
            columns={"연평균기온": "연평균 기온(℃)", "5년_이동평균": "5년 이동평균(℃)"}
        ).round(1),
        use_container_width=True,
        hide_index=True,
    )

st.caption("ⓒ 이 앱은 공개된 서울 기온 데이터를 활용해 만들어졌습니다.")
