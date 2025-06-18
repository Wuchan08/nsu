import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:

    def __init__(self):
        st.title("📊 Bike Sharing Demand EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (train.csv)", type="csv")
        if not uploaded:
            st.info("train.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded, parse_dates=['datetime'])

        tabs = st.tabs([
            "1. 목적 & 절차",
            "2. 데이터셋 설명",
            "3. 데이터 로드 & 품질 체크",
            "4. Datetime 특성 추출",
            "5. 시각화",
            "6. 상관관계 분석",
            "7. 이상치 제거",
            "8. 로그 변환"
        ])

        # 1. 목적 & 분석 절차
        with tabs[0]:
            st.header("🔭 목적 & 분석 절차")
            st.markdown("""
            **목적**: Bike Sharing Demand 데이터셋을 탐색하고,
            다양한 특성이 대여량(count)에 미치는 영향을 파악합니다.

            **절차**:
            1. 데이터 구조 및 기초 통계 확인  
            2. 결측치/중복치 등 품질 체크  
            3. datetime 특성(연도, 월, 일, 시, 요일) 추출  
            4. 주요 변수 시각화  
            5. 변수 간 상관관계 분석  
            6. 이상치 탐지 및 제거  
            7. 로그 변환을 통한 분포 안정화
            """)

        # 2. 데이터셋 설명
        with tabs[1]:
            st.header("🔍 데이터셋 설명")
            st.markdown(f"""
            - **train.csv**: 2011–2012년까지의 시간대별 대여 기록  
            - 총 관측치: {df.shape[0]}개  
            - 주요 변수:
              - **datetime**: 날짜와 시간 (YYYY-MM-DD HH:MM:SS)  
              - **season**: 계절 (1: 봄, 2: 여름, 3: 가을, 4: 겨울)  
              - **holiday**: 공휴일 여부 (0: 평일, 1: 공휴일)  
              - **workingday**: 근무일 여부 (0: 주말/공휴일, 1: 근무일)  
              - **weather**: 날씨 상태  
                - 1: 맑음·부분적으로 흐림  
                - 2: 안개·흐림  
                - 3: 가벼운 비/눈  
                - 4: 폭우/폭설 등  
              - **temp**: 실제 기온 (섭씨)  
              - **atemp**: 체감 온도 (섭씨)  
              - **humidity**: 상대 습도 (%)  
              - **windspeed**: 풍속 (정규화된 값)  
              - **casual**: 비등록 사용자 대여 횟수  
              - **registered**: 등록 사용자 대여 횟수  
              - **count**: 전체 대여 횟수 (casual + registered)
            """)

            st.subheader("1) 데이터 구조 (`df.info()`)")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            st.subheader("2) 기초 통계량 (`df.describe()`)")
            numeric_df = df.select_dtypes(include=[np.number])
            st.dataframe(numeric_df.describe())

            st.subheader("3) 샘플 데이터 (첫 5행)")
            st.dataframe(df.head())

    
    # 3. 데이터 로드 & 품질 체크
        with tabs[2]:
            st.header("3. 데이터 로드 & 품질 체크")

            # (1) 파일 업로드
            uploaded = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
            if uploaded is not None:
                # (2) DataFrame 로드
                df = pd.read_csv(uploaded)

                # ──────────────────────────────────
                # 여기부터 “세종” 결측치 교체, 숫자형 변환, info/describe 출력

                # 3. '세종' 지역의 모든 컬럼에서 '-' → 0 치환
                mask = df['지역'] == '세종'
                df.loc[mask] = df.loc[mask].replace('-', 0)

                # 4. 주요 컬럼을 숫자형으로 변환
                num_cols = ['인구', '출생아수(명)', '사망자수(명)']
                for col in num_cols:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

                # 5. df.info() 출력
                st.subheader("데이터프레임 구조 (`df.info()`)")
                buffer = io.StringIO()
                df.info(buf=buffer)
                st.text(buffer.getvalue())

                # 6. df.describe() 출력
                st.subheader("기초 통계량 (`df.describe()`)")
                st.dataframe(df.describe())
                # ──────────────────────────────────

            # (3)—이후에 다른 품질 체크나 시각화로 넘어가시면 됩니다.
        # 4. Datetime 특성 추출
        with tabs[3]:
            st.header("🕒 Datetime 특성 추출")
            st.markdown("`datetime` 컬럼에서 연, 월, 일, 시, 요일 등을 추출합니다.")

            df['year'] = df['datetime'].dt.year
            df['month'] = df['datetime'].dt.month
            df['day'] = df['datetime'].dt.day
            df['hour'] = df['datetime'].dt.hour
            df['dayofweek'] = df['datetime'].dt.dayofweek

            st.subheader("추출된 특성 예시")
            st.dataframe(df[['datetime', 'year', 'month', 'day', 'hour',
                             'dayofweek']].head())

            # --- 요일 숫자 → 요일명 매핑 (참고용) ---
            day_map = {
                0: '월요일',
                1: '화요일',
                2: '수요일',
                3: '목요일',
                4: '금요일',
                5: '토요일',
                6: '일요일'
            }
            st.markdown("**(참고) dayofweek 숫자 → 요일**")
            # 중복 제거 후 정렬하여 표시
            mapping_df = pd.DataFrame({
                'dayofweek': list(day_map.keys()),
                'weekday': list(day_map.values())
            })
            st.dataframe(mapping_df, hide_index=True)

        # 5. 시각화
        with tabs[4]:
            st.header("Population Trend and Forecast")

            uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
            if uploaded is not None:
                df = pd.read_csv(uploaded)
                df_nat = df[df['지역'] == '전국'].copy()

        # 숫자형 변환
                df_nat['연도'] = pd.to_numeric(df_nat['연도'], errors='coerce').astype(int)
                df_nat['인구'] = pd.to_numeric(df_nat['인구'], errors='coerce')
                df_nat['출생아수(명)'] = pd.to_numeric(df_nat['출생아수(명)'], errors='coerce')
                df_nat['사망자수(명)'] = pd.to_numeric(df_nat['사망자수(명)'], errors='coerce')

        # 정렬 및 실제값 준비
                df_nat.sort_values('연도', inplace=True)
                years = df_nat['연도'].values
                pops = df_nat['인구'].values

        # 최근 3년 자연증가 평균으로 2035 예측
                recent = df_nat.tail(3)
                avg_change = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
                last_year, last_pop = years[-1], pops[-1]
                pop_2035 = last_pop + avg_change * (2035 - last_year)

        # 그래프 그리기
                fig, ax = plt.subplots()
                ax.plot(years, pops, marker='o', label='Actual')
                ax.scatter(2035, pop_2035, marker='X', s=100, label='Forecast 2035')
                ax.set_title("Population Trend with 2035 Forecast")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")
                ax.legend()
                ax.grid(True)

                st.pyplot(fig)
                st.subheader("Regional Population Change Over 5 Years")

                # 1) CSV 재업로드 또는 기존 df 그대로 사용
                uploaded = st.file_uploader("Upload population_trends.csv", type="csv", key="region")
                if uploaded is not None:
                    df = pd.read_csv(uploaded)

                    # 2) 필수 컬럼 숫자형 변환
                    df['연도'] = pd.to_numeric(df['연도'], errors='coerce').astype(int)
                    df['인구'] = pd.to_numeric(df['인구'], errors='coerce')

                    # 3) '전국' 제외
                    df = df[df['지역'] != '전국'].copy()

                    # 4) 최근 5년 전(year_n−5)과 최신(year_n) 구하기
                    years = sorted(df['연도'].unique())
                    year_now = years[-1]
                    year_prev = year_now - 5

                    # 5) 피벗
                    pivot = df[df['연도'].isin([year_prev, year_now])].pivot(
                        index='지역', columns='연도', values='인구'
                    ).dropna()

                    # 6) 변화량·변화율 계산
                    pivot['change'] = pivot[year_now] - pivot[year_prev]
                    pivot['change_thousands'] = pivot['change'] / 1000.0
                    pivot['rate'] = pivot['change'] / pivot[year_prev] * 100

                    # 7) 한국어→영어 매핑
                    region_map = {
                        '서울':'Seoul','부산':'Busan','대구':'Daegu','인천':'Incheon','광주':'Gwangju',
                        '대전':'Daejeon','울산':'Ulsan','세종':'Sejong','경기':'Gyeonggi','강원':'Gangwon',
                        '충북':'Chungbuk','충남':'Chungnam','전북':'Jeonbuk','전남':'Jeonnam',
                        '경북':'Gyeongbuk','경남':'Gyeongnam','제주':'Jeju'
                    }
                    pivot['region_en'] = pivot.index.map(region_map)

                    # 8) 절대 변화량 그래프
                    df1 = pivot.sort_values('change', ascending=False)
                    fig1, ax1 = plt.subplots(figsize=(8, 6))
                    sns.barplot(x='change_thousands', y='region_en', data=df1, ax=ax1)
                    ax1.set_title("Population Change over 5 Years")
                    ax1.set_xlabel("Change (Thousands)")
                    ax1.set_ylabel("Region")
                    for c in ax1.containers:
                        ax1.bar_label(c, fmt="%.1f")
                    ax1.grid(axis='x', linestyle='--', alpha=0.5)
                    st.pyplot(fig1)

                    # 9) 변화율 그래프
                    df2 = pivot.sort_values('rate', ascending=False)
                    fig2, ax2 = plt.subplots(figsize=(8, 6))
                    sns.barplot(x='rate', y='region_en', data=df2, ax=ax2)
                    ax2.set_title("Population Change Rate over 5 Years")
                    ax2.set_xlabel("Change Rate (%)")
                    ax2.set_ylabel("Region")
                    for c in ax2.containers:
                        ax2.bar_label(c, fmt="%.1f%%")
                    ax2.grid(axis='x', linestyle='--', alpha=0.5)
                    st.pyplot(fig2)

                    # 10) 해설
                    st.markdown(
                        "> **Explanation:**\n"
                        "- First chart shows absolute change (in thousands) over the last 5 years, sorted descending.\n"
                        "- Second chart shows percentage change over the same period, sorted descending."
                    )
                    # 여기서부터 Top 100 diff 테이블 코드를 붙여넣으세요.
                    st.subheader("Top 100 Year-Over-Year Population Changes")

                    # 1) 전국 제외 & 숫자형 변환
                    df_reg = df[df['지역'] != '전국'].copy()
                    df_reg['연도'] = pd.to_numeric(df_reg['연도'], errors='coerce').astype(int)
                    df_reg['인구']  = pd.to_numeric(df_reg['인구'], errors='coerce')

                    # 2) 연도별 diff 계산
                    df_reg.sort_values(['지역','연도'], inplace=True)
                    df_reg['diff'] = df_reg.groupby('지역')['인구'].diff()

                    # 3) 절대값 기준 상위 100개 추출
                    df_top = (
                        df_reg
                        .dropna(subset=['diff'])
                        .assign(abs_diff=lambda d: d['diff'].abs())
                        .nlargest(100, 'abs_diff')
                        .drop(columns='abs_diff')
                    )

                    # 4) 한글→영어 지역명 매핑
                    region_map = {
                        '서울':'Seoul','부산':'Busan','대구':'Daegu','인천':'Incheon','광주':'Gwangju',
                        '대전':'Daejeon','울산':'Ulsan','세종':'Sejong','경기':'Gyeonggi','강원':'Gangwon',
                        '충북':'Chungbuk','충남':'Chungnam','전북':'Jeonbuk','전남':'Jeonnam',
                        '경북':'Gyeongbuk','경남':'Gyeongnam','제주':'Jeju'
                    }
                    df_top['region_en'] = df_top['지역'].map(region_map)
                    df_top = df_top[['region_en','연도','diff']].rename(columns={
                        'region_en':'Region', '연도':'Year', 'diff':'Change'
                    })

                    # 5) 스타일링 & 출력
                    styler = (
                        df_top
                        .style
                        .format({'Change': '{:,.0f}'})
                        .background_gradient(
                            cmap='RdBu_r',
                            subset=['Change'],
                            axis=None
                        )
                        .set_properties(subset=['Region','Year'], **{'text-align':'center'})
                    )
                    st.dataframe(styler, height=600)
                    # ──────────────────────────────────
                    # ── Top 100 diff 테이블 아래에 추가 ──
                    st.subheader("Population by Region Over Years (Stacked Area)")

                    # 1) 전국 제외·숫자형 변환·영문 매핑
                    df_area = df[df['지역'] != '전국'].copy()
                    df_area['Year'] = pd.to_numeric(df_area['연도'], errors='coerce').astype(int)
                    df_area['Population'] = pd.to_numeric(df_area['인구'], errors='coerce')
                    region_map = {
                        '서울':'Seoul','부산':'Busan','대구':'Daegu','인천':'Incheon','광주':'Gwangju',
                        '대전':'Daejeon','울산':'Ulsan','세종':'Sejong','경기':'Gyeonggi','강원':'Gangwon',
                        '충북':'Chungbuk','충남':'Chungnam','전북':'Jeonbuk','전남':'Jeonnam',
                        '경북':'Gyeongbuk','경남':'Gyeongnam','제주':'Jeju'
                    }
                    df_area['Region'] = df_area['지역'].map(region_map)

                    # 2) 피벗 테이블 생성 (Year × Region)
                    pivot_area = (
                        df_area
                        .pivot_table(index='Year', columns='Region', values='Population', aggfunc='sum')
                        .fillna(0)
                    )

                    # 3) 누적 영역 그래프 그리기
                    palette = sns.color_palette("tab10", n_colors=len(pivot_area.columns))
                    fig_area, ax_area = plt.subplots(figsize=(10, 6))
                    pivot_area.plot(kind='area', stacked=True, ax=ax_area, color=palette)
                    ax_area.set_title("Population by Region Over Years")
                    ax_area.set_xlabel("Year")
                    ax_area.set_ylabel("Population")
                    ax_area.legend(title="Region", bbox_to_anchor=(1.02, 1), loc='upper left')
                    ax_area.grid(alpha=0.3)

                    # 4) Streamlit에 표시
                    st.pyplot(fig_area)


        # 6. 상관관계 분석
        with tabs[5]:
            st.header("🔗 상관관계 분석")
            # 관심 피처만 선택
            features = ['temp', 'atemp', 'casual', 'registered', 'humidity',
                        'windspeed', 'count']
            corr_df = df[features].corr()

            # 상관계수 테이블 출력
            st.subheader("📊 피처 간 상관계수")
            st.dataframe(corr_df)

            # 히트맵 시각화
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(corr_df, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
            ax.set_xlabel("")  # 축 이름 제거
            ax.set_ylabel("")
            st.pyplot(fig)
            st.markdown(
                "> **해석:**\n"
                "- `count`는 `registered` (r≈0.99) 및 `casual` (r≈0.67)와 강한 양의 상관관계를 보입니다.\n"
                "- `temp`·`atemp`와 `count`는 중간 정도의 양의 상관관계(r≈0.4~0.5)를 나타내며, 기온이 높을수록 대여량이 증가함을 시사합니다.\n"
                "- `humidity`와 `windspeed`는 약한 음의 상관관계(r≈-0.2~-0.3)를 보여, 습도·풍속이 높을수록 대여량이 다소 감소합니다."
            )

        # 7. 이상치 제거
        with tabs[6]:
            st.header("🚫 이상치 제거")
            # 평균·표준편차 계산
            mean_count = df['count'].mean()
            std_count = df['count'].std()
            # 상한치: 평균 + 3*표준편차
            upper = mean_count + 3 * std_count

            st.markdown(f"""
                        - **평균(count)**: {mean_count:.2f}  
                        - **표준편차(count)**: {std_count:.2f}  
                        - **이상치 기준**: `count` > 평균 + 3×표준편차 = {upper:.2f}  
                          (통계학의 68-95-99.7 법칙(Empirical rule)에 따라 평균에서 3σ를 벗어나는 관측치는 전체의 약 0.3%로 극단치로 간주)
                        """)
            df_no = df[df['count'] <= upper]
            st.write(f"- 이상치 제거 전: {df.shape[0]}개, 제거 후: {df_no.shape[0]}개")

        # 8. 로그 변환
        with tabs[7]:
            st.header("🔄 로그 변환")
            st.markdown("""
                **로그 변환 맥락**  
                - `count` 변수는 오른쪽으로 크게 치우친 분포(skewed distribution)를 가지고 있어,  
                  통계 분석 및 모델링 시 정규성 가정이 어렵습니다.  
                - 따라서 `Log(Count + 1)` 변환을 통해 분포의 왜도를 줄이고,  
                  중앙값 주변으로 데이터를 모아 해석력을 높입니다.
                """)

            # 변환 전·후 분포 비교
            fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 4))

            # 원본 분포
            sns.histplot(df['count'], kde=True, ax=axes[0])
            axes[0].set_title("Original Count Distribution")
            axes[0].set_xlabel("Count")
            axes[0].set_ylabel("Frequency")

            # 로그 변환 분포
            df['log_count'] = np.log1p(df['count'])
            sns.histplot(df['log_count'], kde=True, ax=axes[1])
            axes[1].set_title("Log(Count + 1) Distribution")
            axes[1].set_xlabel("Log(Count + 1)")
            axes[1].set_ylabel("Frequency")

            st.pyplot(fig)

            st.markdown("""
                > **그래프 해석:**  
                > - 왼쪽: 원본 분포는 한쪽으로 긴 꼬리를 가진 왜곡된 형태입니다.  
                > - 오른쪽: 로그 변환 후 분포는 훨씬 균형잡힌 형태로, 중앙값 부근에 데이터가 집중됩니다.  
                > - 극단치의 영향이 완화되어 이후 분석·모델링 안정성이 높아집니다.
                """)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()