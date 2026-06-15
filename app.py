import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os

# -------------------------------------------------------------
# 1. 페이지 설정 (최상단에 단 한 번만 정의)
# -------------------------------------------------------------
st.set_page_config(
    page_title="강원도 데이터 종합 분석 대시보드",
    page_icon="🌲",
    layout="wide"
)

# -------------------------------------------------------------
# 2. 데이터베이스 연결 함수 (캐싱 적용 및 3개 DB 완벽 분리)
# -------------------------------------------------------------
@st.cache_data
def run_query_aging(query, params=None):
    """고령화 DB(고령화.db) 연결 함수"""
    try:
        with sqlite3.connect("고령화.db") as conn:
            if params:
                return pd.read_sql_query(query, conn, params=params)
            return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"고령화.db 연결 실패: {e}")
        return pd.DataFrame()

@st.cache_data
def run_query_festival(query, params=None):
    """축제 DB(축제.db) 연결 함수"""
    try:
        with sqlite3.connect("축제.db") as conn:
            if params:
                return pd.read_sql_query(query, conn, params=params)
            return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"축제.db 연결 실패: {e}")
        return pd.DataFrame()

@st.cache_data
def run_query_content(query, params=None):
    """콘텐츠 DB(콘텐츠.db) 연결 함수"""
    try:
        with sqlite3.connect("콘텐츠.db") as conn:
            if params:
                return pd.read_sql_query(query, conn, params=params)
            return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"콘텐츠.db 연결 실패: {e}")
        return pd.DataFrame()


# -------------------------------------------------------------
# 3. 메인 타이틀
# -------------------------------------------------------------
st.title("🌲 강원도 종합 데이터 분석 대시보드")
st.markdown("강원도의 인구 고령화 현황, 지역 레저 및 축제 트렌드, 그리고 외국인 방문객 인사이트를 한눈에 비교 분석합니다.")
st.divider()


# =============================================================
# PART 1: 강원도 고령화 및 지역 경제 (고령화.db 기반)
# =============================================================
st.markdown('<h1 style="font-size: 30px; font-weight: bold; color: #2C3E50;">👵 1. 강원도 지역 경제 및 고령화 현황</h1>', unsafe_allow_html=True)
st.caption("가설: 고령화율이 높을수록 지역 생산성 및 경제 지표가 둔화될 것이다.")

# 고령화.db 존재 여부 체크
if not os.path.exists("고령화.db"):
    st.warning("⚠️ 고령화 파트에 필요한 '고령화.db' 파일을 찾을 수 없어 이 영역의 시각화를 건너뜁니다.")
else:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1-1. 10년간 고령화율 추이 (2014~2023)")
        try:
            # SQL을 이용해 '고령화' 테이블을 직접 불러옵니다.
            df_aging = run_query_aging("SELECT * FROM 고령화")
            
            if not df_aging.empty:
                df_aging.columns = df_aging.columns.str.strip()
                df_aging = df_aging.dropna(subset=['시점']).sort_values('시점')
                df_aging['고령화율'] = (df_aging['고령자_65세이상'] / df_aging['등록인구_소계']) * 100

                fig1_1 = go.Figure()
                fig1_1.add_trace(go.Bar(
                    x=df_aging['시점'], 
                    y=df_aging['고령자_65세이상'], 
                    name='고령자 수 (명)', 
                    yaxis='y1', 
                    marker_color='#FFA07A'
                ))
                fig1_1.add_trace(go.Scatter(
                    x=df_aging['시점'], 
                    y=df_aging['고령화율'], 
                    name='고령화율 (%)', 
                    yaxis='y2', 
                    mode='lines+markers', 
                    line=dict(color='#FF4500', width=3)
                ))
                
                fig1_1.update_layout(
                    yaxis=dict(title='고령자 수 (명)', showgrid=False),
                    yaxis2=dict(title='고령화율 (%)', overlaying='y', side='right', showgrid=True),
                    legend=dict(x=0.01, y=0.99),
                    margin=dict(l=40, r=40, t=20, b=40)
                )
                st.plotly_chart(fig1_1, use_container_width=True)
            else:
                st.warning("'고령화' 테이블에서 데이터를 찾을 수 없습니다.")
        except Exception as e:
            st.error(f"차트 1-1 로드 실패: {e}")

    with col2:
        st.subheader("1-2. 2023년 강원도 인구 구성 현황")
        try:
            # SQL을 이용해 '경제인구' 테이블을 직접 불러옵니다.
            df_economic = run_query_aging("SELECT * FROM 경제인구")
            
            if not df_economic.empty:
                df_economic.columns = df_economic.columns.str.strip()
                df_filtered = df_economic[
                    (df_economic['성별'].str.strip() == '합계') & 
                    (df_economic['분기별'].str.strip() == '전체')
                ]
                
                if not df_filtered.empty:
                    labels = ['취업자', '실업자', '비경제활동(가사/육아)', '비경제활동(통학)', '비경제활동(기타)']
                    row = df_filtered.iloc[0]
                    values = [row['취업자'], row['실업자'], row['비경제활동_가사육아'], row['비경제활동_통학'], row['비경제활동_기타']]
                    
                    fig1_2 = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker=dict(colors=px.colors.qualitative.Pastel1))])
                    fig1_2.update_layout(margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig1_2, use_container_width=True)
                else:
                    st.warning("데이터에서 합계/전체 행을 찾을 수 없습니다.")
            else:
                st.warning("'경제인구' 테이블에서 데이터를 찾을 수 없습니다.")
        except Exception as e:
            st.error(f"차트 1-2 로드 실패: {e}")

    st.info("""
    **💡 인사이트 (가설 1 검증)**
    * 강원도의 고령화율은 지난 10년간 가파르게 상승하여 이미 초고령사회 기준(20%)을 크게 상회하고 있습니다.
    * 경제활동 인구 구조 분석 결과, 생산에 직접 기여하지 못하는 비경제활동 인구 비중이 높아 지역 생산성 전반에 부담으로 작용하고 있음을 시사합니다.
    """)

    st.subheader("1-3. 강원도 주요 산업 구조와 관광 산업의 비중")
    try:
        # SQL을 이용해 'GRDP' 테이블을 직접 불러옵니다.
        df_grdp = run_query_aging("SELECT * FROM GRDP")
        
        if not df_grdp.empty:
            df_grdp.columns = df_grdp.columns.str.strip()
            
            exclude_cats = ['지역내총생산(시장가격)', '순생산물세', '총부가가치(기초가격)', '총부가가치']
            df_grdp_filtered = df_grdp[
                (df_grdp['시도별'].str.contains('강원')) & 
                (~df_grdp['경제활동별'].isin(exclude_cats))
            ].sort_values('실질', ascending=True)
            
            colors = []
            for cat in df_grdp_filtered['경제활동별']:
                if any(keyword in cat for keyword in ['숙박', '음식점', '문화', '서비스', '도소매', '운수']):
                    colors.append('#008080') 
                else:
                    colors.append('#D3D3D3') 
                    
            fig2 = go.Figure(go.Bar(
                x=df_grdp_filtered['실질'],
                y=df_grdp_filtered['경제활동별'],
                orientation='h',
                marker_color=colors
            ))
            
            fig2.update_layout(
                xaxis_title="실질 GRDP (백만 원)",
                yaxis=dict(tickfont=dict(size=11), automargin=True),
                margin=dict(l=50, r=40, t=20, b=40),
                height=600
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("'GRDP' 테이블에서 데이터를 찾을 수 없습니다.")
    except Exception as e:
        st.error(f"차트 2 로드 실패: {e}")

    st.info("""
    **💡 인사이트 (가설 2 검증)**
    * 강원도의 산업별 실질 총생산 구조를 살펴보면, 제조업 기반이 취약한 대신 **'숙박 및 음식점업' 및 '문화/기타 서비스업' 등 관광 관련 산업(청록색 표시)**이 매우 상위권에 위치해 있습니다.
    * 이는 급격한 고령화로 전통적 생산 인구가 감소하더라도, 지역의 특수성을 살린 관광 마케팅 및 서비스 산업 활성화를 통해 경제의 총부가가치를 유의미하게 방어하고 보완할 수 있음을 입증합니다.
    """)


# =============================================================
# PART 2: 강원도 레저 및 지역 축제 (축제.db 기반)
# =============================================================
st.write("---")
st.markdown('<h1 style="font-size: 30px; font-weight: bold; color: #2C3E50;">🏔️ 2. 강원도 레저 및 지역 축제 분석</h1>', unsafe_allow_html=True)

# 2-1) 기후 변화와 실외 레저
st.subheader("2-1. 특정 계절에 편중된 실외형 레저일수록 기후 변화에 따른 매출 변동이 클 것이다.")
target_regions = ["화천", "홍천", "춘천", "인제"]
selected_region = st.selectbox("분석할 지역을 선택해 주세요:", target_regions, index=2, key="festival_region")

query_1 = """
SELECT 기상.지역, 기상.월별, 기상.평균기온, 기상.최고기온, 기상.최저기온, 기상.강수량, 방문자.방문자수
FROM 기상개황 AS 기상
LEFT JOIN 방문자수 AS 방문자
    ON 기상.지역 = 방문자.지역 AND 기상.월별 = 방문자.월별
WHERE 기상.지역 = ?
ORDER BY CAST(REPLACE(기상.월별, '월', '') AS INTEGER);
"""
df1 = run_query_festival(query_1, (selected_region,))

if not df1.empty:
    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    fig1.add_trace(go.Bar(x=df1['월별'], y=df1['방문자수'], name='방문자수 (명)', marker_color='rgba(135, 206, 250, 0.5)'), secondary_y=False)
    fig1.add_trace(go.Scatter(x=df1['월별'], y=df1['평균기온'], name='평균기온 (℃)', mode='lines+markers', line=dict(color='orange', width=3)), secondary_y=True)
    fig1.add_trace(go.Scatter(x=df1['월별'], y=df1['최고기온'], name='최고기온 (℃)', mode='markers', marker=dict(color='red', size=8, symbol='triangle-up')), secondary_y=True)
    fig1.add_trace(go.Scatter(x=df1['월별'], y=df1['최저기온'], name='최저기온 (℃)', mode='markers', marker=dict(color='blue', size=8, symbol='triangle-down')), secondary_y=True)
    fig1.add_trace(go.Scatter(x=df1['월별'], y=df1['강수량'], name='강수량 (mm)', mode='lines+markers', line=dict(color='purple', width=3)), secondary_y=True)

    fig1.update_layout(title_text=f"📊 {selected_region} 지역 기상 개황 및 방문자수 추이", hovermode="x unified")
    fig1.update_yaxes(title_text="방문자수 (명)", secondary_y=False)
    fig1.update_yaxes(title_text="기온 (℃) / 강수량 (mm)", secondary_y=True)
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.info("데이터가 존재하지 않습니다.")

st.success("📝 **인사이트**: 기상 개황과 방문자수 간의 뚜렷한 정량적 상관관계를 도출하기는 어려웠으나, 기상 통제가 어려운 실외 레저 특성상 지자체 개입과 투자가 쉬운 '지역 축제'의 중요성을 재확인하였습니다.")

# 2-2) 지출 상위 지역과 액티비티
st.write("")
st.subheader("2-2. 방문객수 상위 축제는 액티비티형으로, 호수문화권에 밀접할 것이다.")
st.info("📢 **핵심 발견**: 2023~2025년 지출 상위 4개 지역은 **[강릉, 속초, 춘천, 평창]**으로 고정되어 철옹성 구조를 이룹니다.")

query_2 = """
SELECT 연도, 지역, 비율, 순위 FROM (
    SELECT 연도, 지역, 비율, RANK() OVER (PARTITION BY 연도 ORDER BY 비율 DESC) AS 순위 FROM "지역별 지출"
) WHERE 순위 <= 4 ORDER BY 연도, 순위;
"""
df2 = run_query_festival(query_2)

if not df2.empty:
    if df2['비율'].max() <= 1.0:
        df2['비율'] = df2['비율'] * 100.0

    col_d1, col_d2, col_d3 = st.columns(3)
    cols = [col_d1, col_d2, col_d3]
    years = [2023, 2024, 2025]
    color_map = {"강릉": "#FF6B6B", "속초": "#4D96FF", "춘천": "#6BCB77", "평창": "#FFD93D", "타 지역": "#E5E5E5"}

    for i, year in enumerate(years):
        df_year = df2[df2['연도'] == year].copy()
        sum_ratios = df_year['비율'].sum()
        other_ratio = max(0.0, 100.0 - sum_ratios)
        other_row = pd.DataFrame([{'연도': year, '지역': '타 지역', '비율': other_ratio, '순위': 99}])
        df_plot = pd.concat([df_year, other_row], ignore_index=True)

        fig_donut = px.pie(df_plot, values='비율', names='지역', hole=0.4, color='지역', color_discrete_map=color_map, title=f"📅 {year}년 전체 지출 분포")
        fig_donut.update_traces(textinfo='label+value', texttemplate='%{label}<br><b>%{value:.1f}%</b>')
        fig_donut.update_layout(showlegend=(i == 2), margin=dict(t=50, b=10, l=10, r=10))
        cols[i].plotly_chart(fig_donut, use_container_width=True)

# 2-3) 주제별 관광소비 분석
st.write("")
st.subheader("2-3. 음식, 액티비티, 포토스팟 등 통용성이 높은 주제일수록 외국인 방문객 수가 높을 것이다.")

query_3_A = """
SELECT 연도, 월별, 분류, 소비액 FROM 관광소비 WHERE 분류 = '관광총소비' ORDER BY 연도, CAST(REPLACE(월별, '월', '') AS INTEGER);
"""
query_3_B = """
SELECT 소비.연도, 소비.월별, 소비.소비액, 축제.축제명, 축제.지역, 축제.분야, 축제.월별 AS 축제시기
FROM (
    SELECT 연도, 월별, 소비액, RANK() OVER (PARTITION BY 연도 ORDER BY 소비액 DESC) AS 순위 FROM 관광소비 WHERE 분류 = '관광총소비'
) AS 소비
LEFT JOIN 축제 ON CAST(REPLACE(축제.월별, '월', '') AS INTEGER) = CAST(REPLACE(소비.월별, '월', '') AS INTEGER)
WHERE 소비.순위 <= 3 ORDER BY 소비.연도, 소비.소비액 DESC;
"""
df3_A = run_query_festival(query_3_A)
df3_B = run_query_festival(query_3_B)

if not df3_A.empty:
    fig3 = px.line(df3_A, x='월별', y='소비액', color='연도', markers=True, title="📈 연도별/월별 관광총소비액 추이")
    st.plotly_chart(fig3, use_container_width=True)

st.subheader("🏆 연도별 최고 소비액 Top 3 해당 월의 개최 축제 목록")
if not df3_B.empty:
    st.dataframe(df3_B, use_container_width=True)


# =============================================================
# PART 3: 외국인 관광 인사이트 (콘텐츠.db 기반)
# =============================================================
st.write("---")
st.markdown('<h1 style="font-size: 30px; font-weight: bold; color: #2C3E50;">✈️ 3. 외국인 관광객 인사이트</h1>', unsafe_allow_html=True)

if not os.path.exists("콘텐츠.db"):
    st.warning("⚠️ 콘텐츠 파트에 필요한 '콘텐츠.db' 파일을 찾을 수 없어 이 영역의 시각화를 건너뜁니다.")
else:
    # 3-1) 객단가 비교
    st.markdown('<h2 style="font-size: 22px; font-weight: bold; margin-top: 15px; margin-bottom: 10px;">3-1. 외국인·외지인 관광객 객단가 비교</h2>', unsafe_allow_html=True)

    sql1 = """
    SELECT
        ROUND((SELECT SUM(c.지역관광소비액_백만원 * 1000000.0) FROM 외국인관광소비 c WHERE c.기준년월일 BETWEEN 202505 AND 202604) /
              (SELECT SUM(v.방문자수) FROM 외국인방문자수 v WHERE v.기준년월일 BETWEEN 202505 AND 202604), 0) AS 외국인_평균객단가,
        ROUND((SELECT SUM(s.관광소비액_백만원 * 1000000.0) FROM 전국대비관광소비추이외지인 s WHERE s.기준연월 BETWEEN 202505 AND 202604 AND s.지역명 = '강원특별자치도') /
              (SELECT SUM(o.방문자수) FROM 외지인방문자수 o WHERE o.기준년월 BETWEEN 202505 AND 202604), 0) AS 외지인_평균객단가;
    """
    df_c1 = run_query_content(sql1)

    col_c1, col_c2 = st.columns([1, 1])
    with col_c1:
        st.write(f"<style>div[data-testid='stTable'] table {{ font-size: 16px !important; }}</style>", unsafe_allow_html=True)
        st.table(df_c1.style.format("{:,.0f} (원)"))
    with col_c2:
        with st.expander("💻 사용한 SQL 보기"):
            st.code(sql1, language='sql')

    st.markdown(
        """
        <div style="background-color: #f1f9f5; padding: 15px; border-radius: 0.5rem; margin-top: 10px; margin-bottom: 20px;">
            <span style="font-weight: bold; font-size: 1.1em; color: #1e4620;">❓ 가설 설정 & 결과</span><br>
            <div style="color: #212529; line-height: 1.6; font-size: 14px; margin-top: 5px;">
                가설: 외국인 방문객의 객단가가 더 높을 것이다. <br>
                <b>결과: 외지인 방문객보다 오히려 낮게 나타났습니다.</b> 필리핀, 베트남 등 근로 목적 방문자가 섞여 있어 세분화 분석이 요구됩니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3-2) 기여도 상위 국가
    st.write("")
    st.markdown('<h2 style="font-size: 22px; font-weight: bold; margin-bottom: 10px;">3-2. 강원도 방문·소비 통합 기여도 상위 국가</h2>', unsafe_allow_html=True)
    
    sql2 = """
    WITH Avg_Visit AS (
        SELECT 국가, AVG(방문자_비율) AS 평균_방문_비율 FROM 외국인방문합본
        WHERE 국가 <> '기타' AND 연도 BETWEEN 2023 AND 2025 GROUP BY 국가), 
    Avg_Consumption AS (
        SELECT 국가, AVG(소비_비율) AS 평균_소비_비율 FROM 외국인소비합본
        WHERE 국가 <> '기타' AND 연도 BETWEEN 2023 AND 2025 GROUP BY 국가),
    Combined_Metrics AS (
        SELECT V.국가, V.평균_방문_비율, C.평균_소비_비율, (V.평균_방문_비율 + C.평균_소비_비율) AS 총_합산_점수,
        ROW_NUMBER() OVER (ORDER BY (V.평균_방문_비율 + C.평균_소비_비율) DESC) AS 통합_순위
        FROM Avg_Visit V INNER JOIN Avg_Consumption C ON V.국가 = C.국가)
    SELECT 통합_순위, 국가, ROUND(평균_방문_비율, 2) as 평균_방문비율_3개년, ROUND(평균_소비_비율, 2) as 평균_소비비율_3개년, ROUND(총_합산_점수, 2) as 총_합산_점수 
    FROM Combined_Metrics WHERE 통합_순위 <= 3;
    """
    df_c2 = run_query_content(sql2)

    col_c2_1, col_c2_2 = st.columns([2, 1])
    with col_c2_1:
        if not df_c2.empty:
            fig_c2 = px.bar(df_c2, x='국가', y='총_합산_점수', text='총_합산_점수', color='국가', title="강원도 방문 및 소비 비중 상위 국가")
            st.plotly_chart(fig_c2, use_container_width=True)
    with col_c2_2:
        with st.expander("💻 사용한 SQL 보기"):
            st.code(sql2, language='sql')

    # 3-3) 선호 콘텐츠 (Top 3)
    st.write("")
    st.markdown('<h2 style="font-size: 22px; font-weight: bold; margin-bottom: 10px;">3-3. 미국/중국 선호 콘텐츠 (Top 3)</h2>', unsafe_allow_html=True)
    
    col_c3_1, col_c3_2 = st.columns([1, 1])
    with col_c3_1:
        st.markdown(
            """
            <div style="display: flex; justify-content: space-between; width: 100%; margin-top: 5px; margin-bottom: 15px; padding-left: 2px;">
                <div style="width: 50%; text-align: left; font-family: 'Source Sans Pro', sans-serif; color: #31333f; font-weight: 600; font-size: 16px;">미국 선호 콘텐츠</div>
                <div style="width: 50%; text-align: left; font-family: 'Source Sans Pro', sans-serif; color: #31333f; font-weight: 600; font-size: 16px; padding-left: 15px;">중국 선호 콘텐츠</div>
            </div>
            <div style="display: flex; width: 100%; height: 330px; background-color: white; border: 1px solid #eeeeee; border-radius: 4px; box-sizing: border-box;">
                <div style="width: 50%; display: flex; flex-direction: column; justify-content: center; align-items: center; border-right: 1px solid #eeeeee; padding-right: 10px;">
                    <div style="font-size: 80px; font-weight: 900; color: #1e5096; line-height: 1.1; letter-spacing: -2px; margin-bottom: 5px;">뷰티</div>
                    <div style="font-size: 60px; font-weight: 900; color: #64a0dc; line-height: 1.1; letter-spacing: -1px; margin-bottom: 5px;">웹툰</div>
                    <div style="font-size: 60px; font-weight: 900; color: #64a0dc; line-height: 1.1; letter-spacing: -1px;">패션</div>
                </div>
                <div style="width: 50%; display: flex; flex-direction: column; justify-content: center; align-items: center; padding-left: 10px;">
                    <div style="font-size: 83px; font-weight: 900; color: #8b0000; line-height: 1.1; letter-spacing: -2px; margin-bottom: 5px;">뷰티</div>
                    <div style="font-size: 73px; font-weight: 900; color: #e03a3a; line-height: 1.1; letter-spacing: -1px; margin-bottom: 5px;">패션</div>
                    <div style="font-size: 48px; font-weight: 900; color: #f39292; line-height: 1.1; letter-spacing: -1px;">드라마</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_c3_2:
        sql3 = """
        WITH Avg_Content_Consumption AS (
            SELECT 조사국가명 AS 국가, 콘텐츠URL AS 콘텐츠종류, AVG(CAST(전체총합수 AS DECIMAL(10,2))) AS 평균_소비_비중
            FROM 한국문화콘텐츠소비
            WHERE 조사국가명 IN ('미국', '중국') AND 보고서년도내용 IN ('2023', '2024', '2025') AND 항목명 LIKE '%비중%'
            GROUP BY 조사국가명, 콘텐츠URL),
        Ranked_Content AS (
            SELECT 국가, 콘텐츠종류, 평균_소비_비중, ROW_NUMBER() OVER (PARTITION BY 국가 ORDER BY 평균_소비_비중 DESC) AS 콘텐츠_순위
            FROM Avg_Content_Consumption)
        SELECT 국가, 콘텐츠_순위 AS 순위, 콘텐츠종류, ROUND(평균_소비_비중, 2) AS 평균_소비비중_퍼센트
        FROM Ranked_Content WHERE 콘텐츠_순위 <= 3;
        """
        with st.expander("💻 사용한 SQL 보기"):
            st.code(sql3, language="sql")

    # 3-4) 소비 트렌드 비교
    st.write("")
    st.markdown('<h2 style="font-size: 22px; font-weight: bold; margin-bottom: 10px;">3-4. 외국인 관광객 소비 패턴 분석</h2>', unsafe_allow_html=True)

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown('<div style="font-size:16px; font-weight:600; color:#31333F; margin-bottom:8px;">📍 강원도 내 소비 비율</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div style="background-color: white; border: 1px solid #eeeeee; border-radius: 4px; padding: 18px; height: 350px; display: flex; flex-direction: column; justify-content: space-between; font-family: sans-serif;">
                <div>
                    <div style="font-size: 14px; font-weight: bold; color: #333333; margin-bottom: 8px; text-align: left;">2023년</div>
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div style="width: 70px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">쇼핑업</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 18px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #2b5c8f; width: 47.8%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">23.9%</div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div style="width: 70px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">식음료업</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 18px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #2b5c8f; width: 48.8%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">24.4%</div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <div style="width: 70px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">숙박업</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 18px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #2b5c8f; width: 76.6%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">38.3%</div>
                    </div>
                </div>
                <hr style="margin: 10px 0; border: none; border-top: 1px dashed #dddddd;">
                <div>
                    <div style="font-size: 14px; font-weight: bold; color: #333333; margin-bottom: 8px; text-align: left;">2024년</div>
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div style="width: 70px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">쇼핑업</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 18px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #4682b4; width: 49.8%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">24.9%</div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div style="width: 70px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">식음료업</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 18px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #4682b4; width: 56.4%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">28.2%</div>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <div style="width: 70px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">숙박업</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 18px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #4682b4; width: 64.8%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">32.4%</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_right:
        st.markdown('<div style="font-size:16px; font-weight:600; color:#31333F; margin-bottom:8px;">🇰🇷 전국 소비 금액 (억 원)</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div style="background-color: white; border: 1px solid #eeeeee; border-radius: 4px; padding: 18px; height: 350px; display: flex; flex-direction: column; justify-content: space-between; font-family: sans-serif;">
                <div>
                    <div style="font-size: 14px; font-weight: bold; color: #333333; margin-bottom: 6px; text-align: left;">2023년</div>
                    <div style="display: flex; align-items: center; margin-bottom: 6px;">
                        <div style="width: 80px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">식음료비</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 15px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #a2d149; width: 30.4%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">288.9</div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 6px;">
                        <div style="width: 80px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">숙박비</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 15px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #a2d149; width: 46.2%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">439.1</div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 6px;">
                        <div style="width: 80px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">쇼핑비</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 15px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #a2d149; width: 47.7%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">453.3</div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 6px;">
                        <div style="width: 80px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">국제 교통비</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 15px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #a2d149; width: 78.4%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">745.2</div>
                    </div>
                </div>
                <hr style="margin: 8px 0; border: none; border-top: 1px dashed #dddddd;">
                <div>
                    <div style="font-size: 14px; font-weight: bold; color: #333333; margin-bottom: 6px; text-align: left;">2024년</div>
                    <div style="display: flex; align-items: center; margin-bottom: 6px;">
                        <div style="width: 80px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">식음료비</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 15px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #8bc34a; width: 27.2%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">258.6</div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 6px;">
                        <div style="width: 80px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">숙박비</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 15px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #8bc34a; width: 39.7%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">377.8</div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 6px;">
                        <div style="width: 80px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">쇼핑비</div>
                        <div style="flex-grow: 1; background-color: #8bc34a; width: 46.2%; height: 100%;"></div>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <div style="width: 80px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">국제 교통비</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 15px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #8bc34a; width: 65.0%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">617.7</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 3-5) 쇼핑 업종 상세 분석
    st.write("")
    st.markdown('<h2 style="font-size: 22px; font-weight: bold; margin-bottom: 10px;">3-5. 강원도 외국인 관광객 쇼핑 유형 분석</h2>', unsafe_allow_html=True)
    
    sql6 = """
    WITH Ranked_Shopping_Subcategory AS (
        SELECT 
            연도, 
            "카테고리 대분류" AS 대분류, 
            "카테고리 중분류" AS 중분류, 
            "카테고리 중분류 소비 비율" AS 중분류_소비_비율,
            ROW_NUMBER() OVER (PARTITION BY 연도 ORDER BY "카테고리 중분류 소비 비율" DESC) AS 순위
        FROM 강원도소비유형합본 
        WHERE "카테고리 대분류" = '쇼핑업' AND 연도 IN (2023, 2024)
    )
    SELECT 연도, 순위, 중분류, CAST(ROUND(중분류_소비_비율, 1) AS VARCHAR) || '%' AS 중분류_소비_비율
    FROM Ranked_Shopping_Subcategory WHERE 순위 <= 3 ORDER BY 연도 ASC, 순위 ASC;
    """
    df6 = run_query_content(sql6)

    쇼핑_상세_data = pd.DataFrame([
        {"연도": "2023", "중분류": "기타관광쇼핑", "비율": "64.3%"},
        {"연도": "2023", "중분류": "대형쇼핑몰", "비율": "26.8%"},
        {"연도": "2023", "중분류": "레저용품쇼핑", "비율": "8.7%"},
        {"연도": "2024", "중분류": "기타관광쇼핑", "비율": "64.8%"},
        {"연도": "2024", "중분류": "대형쇼핑몰", "비율": "25.3%"},
        {"연도": "2024", "중분류": "레저용품쇼핑", "비율": "9.8%"}
    ])

    col_g, col_t = st.columns([1.2, 0.8])
    with col_g:
        st.markdown(
            """
            <div style="background-color: white; border: 1px solid #eeeeee; border-radius: 4px; padding: 18px; height: 350px; display: flex; flex-direction: column; justify-content: space-between; font-family: sans-serif;">
                <div>
                    <div style="font-size: 14px; font-weight: bold; color: #333333; margin-bottom: 8px; text-align: left;">2023년 쇼핑 업종별 비중</div>
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div style="width: 95px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">레저용품쇼핑</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 18px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #E67E22; width: 10.8%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">8.7%</div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div style="width: 95px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">대형쇼핑몰</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 18px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #E67E22; width: 33.5%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">26.8%</div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <div style="width: 95px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">기타관광쇼핑</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 18px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #E67E22; width: 80.3%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">64.3%</div>
                    </div>
                </div>
                <hr style="margin: 10px 0; border: none; border-top: 1px dashed #dddddd;">
                <div>
                    <div style="font-size: 14px; font-weight: bold; color: #333333; margin-bottom: 8px; text-align: left;">2024년 쇼핑 업종별 비중</div>
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div style="width: 95px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">레저용품쇼핑</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 18px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #F39C12; width: 12.2%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">9.8%</div>
                    </div>
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div style="width: 95px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">대형쇼핑몰</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 18px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #F39C12; width: 31.6%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">25.3%</div>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <div style="width: 95px; font-size: 13px; color: #444444; text-align: right; padding-right: 10px; font-weight: bold;">기타관광쇼핑</div>
                        <div style="flex-grow: 1; background-color: #f0f2f6; height: 18px; border-radius: 2px; overflow: hidden;">
                            <div style="background-color: #F39C12; width: 81.0%; height: 100%;"></div>
                        </div>
                        <div style="width: 55px; font-size: 13px; font-weight: bold; color: #333333; padding-left: 8px;">64.8%</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_t:
        st.write(f"<style>div[data-testid='stDataFrame'] table {{ font-size: 15px !important; }}</style>", unsafe_allow_html=True)
        st.dataframe(쇼핑_상세_data, use_container_width=True, hide_index=True)

    # 3-6) 뷰티/패션 접근 경로
    st.write("")
    st.markdown('<h2 style="font-size: 22px; font-weight: bold; margin-bottom: 10px;">3-6. 외국인 뷰티/패션 접근 경로</h2>', unsafe_allow_html=True)

    query_fashion = """
    SELECT 
        SUM(CASE WHEN IQ2_1 = 0 THEN 1 ELSE 0 END) AS "소셜네트워크서비스",
        SUM(CASE WHEN IQ2_2 = 0 THEN 1 ELSE 0 END) AS "드라마, 예능, 영화",
        SUM(CASE WHEN IQ2_3 = 0 THEN 1 ELSE 0 END) AS "자국 패션 쇼, 전시회",
        SUM(CASE WHEN IQ2_4 = 0 THEN 1 ELSE 0 END) AS "유튜브",
        SUM(CASE WHEN IQ2_5 = 0 THEN 1 ELSE 0 END) AS "온/오프라인 판매처",
        SUM(CASE WHEN IQ2_6 = 0 THEN 1 ELSE 0 END) AS "책, 잡지,기사",
        SUM(CASE WHEN IQ2_7 = 0 THEN 1 ELSE 0 END) AS "기타"
    FROM "해외한류" WHERE SQ1a = 1 OR SQ1a = 13;
    """
    query_beauty = """
    SELECT 
        SUM(CASE WHEN JQ2_1 = 0 THEN 1 ELSE 0 END) AS "소셜네트워크서비스",
        SUM(CASE WHEN JQ2_2 = 0 THEN 1 ELSE 0 END) AS "드라마, 예능, 영화",
        SUM(CASE WHEN JQ2_3 = 0 THEN 1 ELSE 0 END) AS "자국 뷰티 쇼, 전시회",
        SUM(CASE WHEN JQ2_4 = 0 THEN 1 ELSE 0 END) AS "유튜브",
        SUM(CASE WHEN JQ2_5 = 0 THEN 1 ELSE 0 END) AS "온/오프라인 판매처",
        SUM(CASE WHEN JQ2_6 = 0 THEN 1 ELSE 0 END) AS "책, 잡지,기사",
        SUM(CASE WHEN JQ2_7 = 0 THEN 1 ELSE 0 END) AS "기타"
    FROM "해외한류" WHERE SQ1a = 1 OR SQ1a = 13;
    """

    df_fashion = run_query_content(query_fashion)
    df_beauty = run_query_content(query_beauty)

    if not df_fashion.empty and not df_beauty.empty:
        df_fashion_melted = df_fashion.melt(var_name="접근경로", value_name="빈도수")
        df_beauty_melted = df_beauty.melt(var_name="접근경로", value_name="빈도수")

        df_fashion_sorted = df_fashion_melted.sort_values(by="빈도수", ascending=False)
        strong_colors = ['#ff6b81', '#2ed573', '#ffa502']
        text_strong_colors = ['#d63031', '#10ac84', '#ff7f50']

        fashion_color_map = {}
        for i, (idx, row) in enumerate(df_fashion_sorted.iterrows()):
            path_name = row['접근경로']
            fashion_color_map[path_name] = strong_colors[i] if i < 3 else '#e0e0e0'

        df_fashion_melted['차트레이블'] = df_fashion_melted.apply(
            lambda r: f"<b>{r['접근경로']}</b>" if list(df_fashion_sorted['접근경로']).index(r['접근경로']) < 3 else r['접근경로'], axis=1
        )

        df_beauty_sorted = df_beauty_melted.sort_values(by="빈도수", ascending=False)
        beauty_color_map = {}
        for i, (idx, row) in enumerate(df_beauty_sorted.iterrows()):
            path_name = row['접근경로']
            beauty_color_map[path_name] = strong_colors[i] if i < 3 else '#e0e0e0'

        df_beauty_melted['차트레이블'] = df_beauty_melted.apply(
            lambda r: f"<b>{r['접근경로']}</b>" if list(df_beauty_sorted['접근경로']).index(r['접근경로']) < 3 else r['접근경로'], axis=1
        )

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            fig_f = px.pie(df_fashion_melted, values='빈도수', names='차트레이블', title='👚 한국 패션 콘텐츠 유입 경로 (TOP 3 강조)', hole=0.3,
                           color='차트레이블', color_discrete_map={f"<b>{k}</b>" if list(df_fashion_sorted['접근경로']).index(k) < 3 else k: v for k, v in fashion_color_map.items()})
            st.plotly_chart(fig_f, use_container_width=True)
        with col_p2:
            fig_b = px.pie(df_beauty_melted, values='빈도수', names='차트레이블', title='💄 한국 뷰티 콘텐츠 유입 경로 (TOP 3 강조)', hole=0.3,
                           color='차트레이블', color_discrete_map={f"<b>{k}</b>" if list(df_beauty_sorted['접근경로']).index(k) < 3 else k: v for k, v in beauty_color_map.items()})
            st.plotly_chart(fig_b, use_container_width=True)

    st.success("""
    📝 **외국인 관광객 종합 인사이트**:  
    * 미국/중국 관광객 모두 뷰티, 패션 등 K-라이프스타일 콘텐츠 선호도가 압도적으로 나타납니다.
    * 유입 경로의 주력 채널인 '유튜브(YouTube)' 마케팅과 함께 숙박, 미식(식음료), 기념품 쇼핑(기타관광쇼핑)을 통합적으로 연계하는 강원도 전용 콘텐츠 기획이 효과적일 것으로 사료됩니다.
    """)

# =============================================================
# 4. 대시보드 푸터
# =============================================================
st.divider()
st.caption("💻 강원도 지역 분석 통합 대시보드 v2.0 | 개발 환경: Python 3.x, SQLite, Streamlit")