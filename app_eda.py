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
        st.title("Population Trends EDA")

        # 1) CSV 파일 업로드
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload the population_trends.csv file.")
            return

        # 2) 데이터 로드 및 결측 처리
        df = pd.read_csv(uploaded)  
        # '-' 문자열을 일단 NaN으로 간주
        df.replace('-', np.nan, inplace=True)

        # ‘세종’ 지역에 한해 모든 NaN → 0
        mask_sejong = df['지역'] == '세종'
        df.loc[mask_sejong] = df.loc[mask_sejong].fillna(0)

        # 3) 열 타입 정리
        # 연도 정수화
        df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
        # 주요 수치형 열 숫자 변환
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 4) 한글→영문 지역명 매핑
        mapping = {
            '전국':'National','서울':'Seoul','부산':'Busan','대구':'Daegu','인천':'Incheon',
            '광주':'Gwangju','대전':'Daejeon','울산':'Ulsan','세종':'Sejong',
            '경기':'Gyeonggi','강원':'Gangwon','충북':'Chungbuk','충남':'Chungnam',
            '전북':'Jeonbuk','전남':'Jeonnam','경북':'Gyeongbuk','경남':'Gyeongnam','제주':'Jeju'
        }
        df['region_en'] = df['지역'].map(mapping)

        # 5) 탭 생성
        tabs = st.tabs([
            "🔢 기초 통계",
            "📈 연도별 추이",
            "🌍 지역별 분석",
            "⚖️ 변화량 분석",
            "🎨 시각화"
        ])

        # --- Tab 1: 기초 통계 ---
        with tabs[0]:
            st.header("기초 통계")
            st.subheader("요약 통계")
            st.write(df.describe(include='all'))
            st.subheader("결측치 개수")
            st.write(df.isnull().sum())
            st.subheader("중복 행 개수")
            st.write(f"{df.duplicated().sum():,} rows")


        # --- Tab 2: 연도별 추이 + 예측 ---
        with tabs[1]:
            st.header("연도별 전체 인구 추이 및 2035 예측")

            # 'National' 데이터 준비
            national = df[df['region_en'] == 'National'].sort_values('연도')
            years = national['연도'].values
            pops = national['인구'].values

            # 최근 3년 출생-사망 순변화 평균 계산
            recent = national.tail(3)
            net_changes = recent['출생아수(명)'] - recent['사망자수(명)']
            avg_net = net_changes.mean()

            last_year = int(recent['연도'].iloc[-1])
            last_pop = float(recent['인구'].iloc[-1])

            # 2035년까지 예측 연도 및 값
            pred_years = np.arange(last_year + 1, 2036)
            pred_pops = last_pop + avg_net * (pred_years - last_year)

            # 그래프 그리기
            fig, ax = plt.subplots()
            ax.plot(years, pops, marker='o', label='Actual')
            ax.plot(pred_years, pred_pops, marker='x', linestyle='--', color='gray', label='Predicted')
            # 2035 예측 점 강조
            pop2035 = last_pop + avg_net * (2035 - last_year)
            ax.scatter(2035, pop2035, s=50, color='red')
            ax.text(2035, pop2035, f"{int(pop2035):,}", va='bottom', ha='right')

            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.set_title("Yearly National Population with 2035 Forecast")
            ax.legend()
            st.pyplot(fig)
    

        # --- Tab 3: 지역별 분석 ---
        with tabs[2]:
            st.header("Regional 5-Year Population Changes")

            # 1) 영어 지역명 매핑
            mapping = {
                '서울':'Seoul','부산':'Busan','대구':'Daegu','인천':'Incheon',
                '광주':'Gwangju','대전':'Daejeon','울산':'Ulsan','세종':'Sejong',
                '경기':'Gyeonggi','강원':'Gangwon','충북':'Chungbuk','충남':'Chungnam',
                '전북':'Jeonbuk','전남':'Jeonnam','경북':'Gyeongbuk','경남':'Gyeongnam','제주':'Jeju'
            }
            df['region_en'] = df['지역'].map(mapping)

            # 2) 최근 5년 구간 계산
            last_year = int(df['연도'].max())
            first_year = last_year - 5
            df5 = df[df['연도'].isin([first_year, last_year])]

            # 3) 절대 변화량
            piv = df5.pivot_table(index='region_en', columns='연도', values='인구')
            piv = piv.drop('National', errors='ignore').dropna()
            piv['change'] = piv[last_year] - piv[first_year]
            piv = piv.sort_values('change', ascending=False)

            # 4) 수평 막대 — 절대 변화량 (단위: 천명)
            fig1, ax1 = plt.subplots()
            sns.barplot(x=piv['change'] / 1000,
                        y=piv.index,
                        ax=ax1)
            for i, v in enumerate(piv['change'] / 1000):
                ax1.text(v, i, f"{v:.1f}", va='center')
            ax1.set_xlabel("Change (Thousands)")
            ax1.set_ylabel("")              # no Korean
            ax1.set_title("5-Year Absolute Change by Region")
            st.pyplot(fig1)
            st.write(
                "This chart ranks regions (excluding National) by absolute "
                "population change over the last 5 years."
            )

            # 5) 변화율 계산
            piv['rate'] = piv['change'] / piv[first_year] * 100

            # 6) 수평 막대 — 변화율 (%)
            fig2, ax2 = plt.subplots()
            sns.barplot(x=piv['rate'],
                        y=piv.index,
                        ax=ax2)
            for i, v in enumerate(piv['rate']):
                ax2.text(v, i, f"{v:.1f}%", va='center')
            ax2.set_xlabel("Growth Rate (%)")
            ax2.set_ylabel("")
            ax2.set_title("5-Year Growth Rate by Region")
            st.pyplot(fig2)
            st.write(
                "This chart shows the percentage growth (or decline) of each region’s "
                "population relative to five years ago."
            )
        # --- Tab 4: 변화량 분석 ---
        with tabs[3]:
            st.header("연도별 인구 증감 상위 100 사례")
            df_diff = df[df['region_en'] != 'National'].copy()
            df_diff = df_diff.sort_values(['region_en','연도'])
            df_diff['diff'] = df_diff.groupby('region_en')['인구'].diff()
            df_top = df_diff.nlargest(100, 'diff')[['region_en','연도','diff']].dropna()

            # 양수·음수에 따른 컬러 함수
            def color_diff(val):
                return 'background-color: #3182bd' if val >= 0 else 'background-color: #de2d26'

            styled = (
                df_top.style
                      .applymap(color_diff, subset=['diff'])
                      .format({'diff': '{:,.0f}'})
            )
            st.dataframe(styled)

        # --- Tab 5: 시각화 ---
        with tabs[4]:
            st.header("누적 영역 그래프 (Region × Year)")
            pivot = df.pivot_table(
                index='연도', columns='region_en', values='인구'
            ).fillna(0)

            colors = sns.color_palette('tab20', n_colors=len(pivot.columns))
            fig, ax = plt.subplots(figsize=(10,6))
            pivot.plot.area(ax=ax, color=colors)
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.set_title("Stacked Area Chart by Region")
            ax.legend(loc='upper left', bbox_to_anchor=(1.0,1.0))
            st.pyplot(fig)

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