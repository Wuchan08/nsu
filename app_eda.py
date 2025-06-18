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

        # 1. 목적 & 절차
        with tabs[0]:
            st.header("🎯 목적 & 절차")
            st.markdown("""
            - 자전거 대여 수요 예측을 위한 탐색적 데이터 분석(EDA)을 수행합니다.  
            - 절차: 데이터 로드 → 결측/중복 확인 → 날짜 특성 추출 → 시각화 → 상관관계 분석 → 이상치 제거 → 로그 변환
            """)

        # 2. 데이터셋 설명
        with tabs[1]:
            st.header("ℹ️ 데이터셋 설명")
            st.write(df.head())
            st.markdown(df.describe().to_markdown())

        # 3. 데이터 로드 & 품질 체크
        with tabs[2]:
            st.header("📂 데이터 로드 & 품질 체크")
            st.write("결측치 개수:", df.isnull().sum().sum())
            st.write("중복 행 개수:", df.duplicated().sum())

        # 4. Datetime 특성 추출
        with tabs[3]:
            st.header("⏳ Datetime 특성 추출")
            df['year']      = df['datetime'].dt.year
            df['month']     = df['datetime'].dt.month
            df['day']       = df['datetime'].dt.day
            df['hour']      = df['datetime'].dt.hour
            df['dayofweek'] = df['datetime'].dt.dayofweek
            st.dataframe(df[['datetime','year','month','day','hour','dayofweek']].head())

        # 5. 시각화
        with tabs[4]:
            st.header("📈 시각화")
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            sns.histplot(df['count'], kde=True, ax=axes[0])
            axes[0].set_title("Count Distribution")
            sns.histplot(np.log1p(df['count']), kde=True, ax=axes[1])
            axes[1].set_title("Log(Count + 1) Distribution")
            st.pyplot(fig)
            st.markdown("> 원본 분포 대비 로그 변환 분포가 훨씬 균형잡힌 형태를 보입니다.")

        # 6. 상관관계 분석
        with tabs[5]:
            st.header("🔗 상관관계 분석")
            features = ['temp','atemp','humidity','windspeed','count']
            corr_df = df[features].corr()
            fig, ax = plt.subplots()
            sns.heatmap(corr_df, annot=True, fmt=".2f", ax=ax)
            ax.set_title("Correlation Matrix")
            st.pyplot(fig)

        # 7. 이상치 제거
        with tabs[6]:
            st.header("🚫 이상치 제거")
            mean_c = df['count'].mean()
            std_c  = df['count'].std()
            df_clean = df[(df['count'] >= mean_c - 3*std_c) & (df['count'] <= mean_c + 3*std_c)]
            st.write(f"제거 전: {df.shape[0]} rows → 제거 후: {df_clean.shape[0]} rows")

        # 8. 로그 변환
        with tabs[7]:
            st.header("🔄 로그 변환")
            df['log_count'] = np.log1p(df['count'])
            fig, axes = plt.subplots(1, 2, figsize=(12,4))
            sns.histplot(df['count'], ax=axes[0], kde=True)
            axes[0].set_title("Original")
            sns.histplot(df['log_count'], ax=axes[1], kde=True)
            axes[1].set_title("Log(Count+1)")
            st.pyplot(fig)

        # ─────────────────────────────────────────────────
        # 아래부터 Population Trends Analysis 탭
        # ─────────────────────────────────────────────────
        st.header("🌍 Population Trends Analysis")
        pop_file = st.file_uploader("Upload population_trends.csv", type="csv")
        if not pop_file:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        pop_df = pd.read_csv(pop_file)

        # 숫자로 변환할 컬럼만 안전하게 선택
        num_cols = ['인구']
        if {'출생아수(명)','사망자수(명)'}.issubset(pop_df.columns):
            num_cols += ['출생아수(명)','사망자수(명)']
        pop_df[num_cols] = pop_df[num_cols].apply(pd.to_numeric, errors='coerce')

        pop_tabs = st.tabs(["Basic Stats","Yearly Trend","Regional Analysis","Change Analysis","Visualization"])

        # Basic Stats
        with pop_tabs[0]:
            st.subheader("1. Missing & Duplicates")
            st.write(pop_df.isnull().sum())
            st.write(f"Duplicates: {pop_df.duplicated().sum()}")

        # Yearly Trend
        with pop_tabs[1]:
            st.subheader("2. Yearly National Population Trend")
            df_nat = pop_df[pop_df['지역']=='전국']
            fig, ax = plt.subplots()
            sns.lineplot(data=df_nat, x='연도', y='인구', marker='o', ax=ax)
            ax.set_title("National Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")

            # 2035 예측 (출생·사망 컬럼이 있을 때만)
            if {'출생아수(명)','사망자수(명)'}.issubset(df_nat.columns):
                recent = df_nat.sort_values('연도').tail(3)
                avg_net = (recent['출생아수(명)'] - recent['사망자수(명)']).mean()
                last_year = recent['연도'].iloc[-1]
                last_pop  = recent['인구'].iloc[-1]
                years_to  = 2035 - last_year
                pred      = last_pop + avg_net * years_to
                ax.scatter(2035, pred, color='red')
                ax.annotate(f"2035: {int(pred):,}", (2035, pred),
                            textcoords="offset points", xytext=(5,5))
            else:
                st.info("Births/deaths data not available → skipping 2035 prediction")

            st.pyplot(fig)

        # Regional Analysis
        with pop_tabs[2]:
            st.subheader("3. 5-Year Population Change by Region")
            latest = pop_df['연도'].max()
            prev   = latest - 5
            df_l   = pop_df[pop_df['연도']==latest]
            df_p   = pop_df[pop_df['연도']==prev]
            df_m   = df_l.merge(df_p, on='지역', suffixes=('_now','_5yrs'))
            df_m   = df_m[df_m['지역']!='전국']
            df_m['change'] = (df_m['인구_now'] - df_m['인구_5yrs'])/1000

            mapping = {'서울':'Seoul','부산':'Busan','대구':'Daegu','인천':'Incheon',
                       '광주':'Gwangju','대전':'Daejeon','울산':'Ulsan','세종':'Sejong'}
            df_m['region_en'] = df_m['지역'].map(mapping).fillna(df_m['지역'])
            df_plot = df_m.sort_values('change', ascending=False)

            fig2, ax2 = plt.subplots()
            sns.barplot(data=df_plot, x='change', y='region_en', ax=ax2)
            ax2.set_xlabel("Change (thousands)")
            ax2.set_ylabel("Region")
            for p in ax2.patches:
                ax2.text(p.get_x()+p.get_width()+0.1,
                         p.get_y()+p.get_height()/2,
                         f"{p.get_width():.1f}", va='center')
            st.pyplot(fig2)

        # Change Analysis
        with pop_tabs[3]:
            st.subheader("4. Top 100 Yearly Population Changes")
            pop_df['diff'] = pop_df.groupby('지역')['인구'].diff()
            df_diff = pop_df[pop_df['지역']!='전국'].dropna().nlargest(100,'diff')
            st.dataframe(
                df_diff.style.background_gradient(subset=['diff'], cmap='Blues')
                       .format({'diff':'{:,}'})
            )

        # Visualization
        with pop_tabs[4]:
            st.subheader("5. Stacked Area Chart by Region")
            pivot = pop_df.pivot(index='연도', columns='지역', values='인구')
            pivot.columns = [mapping.get(col, col) for col in pivot.columns]
            fig3, ax3 = plt.subplots()
            pivot.plot.area(ax=ax3)
            ax3.set_title("Population by Region")
            ax3.set_xlabel("Year")
            ax3.set_ylabel("Population")
            st.pyplot(fig3)


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