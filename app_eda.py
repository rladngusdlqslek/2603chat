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
        st.title("📊 population_trends EDA")
        uploaded = st.file_uploader("population_trends.csv", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded)

        sejong_mask = df['지역'] == '세종'
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            df.loc[sejong_mask, col] = df.loc[sejong_mask, col].replace('-', '0')
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        tabs = st.tabs([
            "1. 기초 통계",
            "2. 연도별 추이",
            "3. 지역별분석",
            "4. 변화량 분석",
            "5. 시각화"
        ])

        # 1. 기초 통계
        with tabs[0]:
            st.header("🔍 데이터 구조 및 요약 통계")

            # df.info() 출력
            buffer = io.StringIO()
            df.info(buf=buffer)
            s = buffer.getvalue()
            st.text(s)

            # df.describe() 출력 (수치형 컬럼)
            st.subheader("기본 통계량 (describe)")
            st.dataframe(df.describe())

        # 2. 연도별 추이
        with tabs[1]:
            st.header("Yearly Total Population Trend")

            # '전국' 필터링
            df_nation = df[df['지역'] == '전국'].copy()

            # 연도별 인구 합계 (사실 '전국'이라서 이미 합계임)
            pop_by_year = df_nation.groupby('연도')['인구'].sum().reset_index()

            # 최근 3년 데이터 (최근 연도 기준으로)
            recent_years = sorted(pop_by_year['연도'].unique())[-3:]
            recent_data = pop_by_year[pop_by_year['연도'].isin(recent_years)].copy()

            # 최근 3년 출생아수, 사망자수 평균 계산
            birth_recent = df_nation[df_nation['연도'].isin(recent_years)].groupby('연도')['출생아수(명)'].sum()
            death_recent = df_nation[df_nation['연도'].isin(recent_years)].groupby('연도')['사망자수(명)'].sum()

            avg_birth = birth_recent.mean()
            avg_death = death_recent.mean()

            # 마지막 연도 인구
            last_year = pop_by_year['연도'].max()
            last_pop = pop_by_year.loc[pop_by_year['연도'] == last_year, '인구'].values[0]

            # 2035년까지 예측 (선형 간단 모델: 매년 인구 = 이전 인구 + (출생 - 사망) 수)
            years_future = list(range(last_year + 1, 2036))
            pop_forecast = []
            pop_curr = last_pop

            for y in years_future:
                pop_curr = pop_curr + (avg_birth - avg_death)
                pop_forecast.append(pop_curr)

            # 예측 데이터프레임 생성
            df_forecast = pd.DataFrame({
                '연도': years_future,
                '인구': pop_forecast
            })

            # 원 데이터와 예측 데이터 합치기
            pop_all = pd.concat([pop_by_year[['연도', '인구']], df_forecast], ignore_index=True)

            # 그래프 그리기
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.lineplot(data=pop_all, x='연도', y='인구', ax=ax, marker='o', label='Population')
            ax.axvline(x=2035, color='red', linestyle='--', label='Year 2035')
            ax.text(2035, pop_forecast[-1], f"{int(pop_forecast[-1]):,}", color='red', va='bottom')

            ax.set_title("Yearly Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")

            st.pyplot(fig)

        # 3. 지역별 분석
        with tabs[2]:
            st.header("Population Change by Region (Last 5 Years)")

            # 최근 5년 데이터 (최대 연도 기준)
            max_year = df['연도'].max()
            recent_years = list(range(max_year - 4, max_year + 1))

            df_recent = df[df['연도'].isin(recent_years)].copy()

            # '전국' 제외
            df_recent = df_recent[df_recent['지역'] != '전국']

            # 지역별 5년 전과 최근 인구
            pop_start = df_recent[df_recent['연도'] == recent_years[0]][['지역', '인구']].set_index('지역')
            pop_end = df_recent[df_recent['연도'] == recent_years[-1]][['지역', '인구']].set_index('지역')

            # 인구 변화량 계산
            pop_change = (pop_end['인구'] - pop_start['인구']).sort_values(ascending=False)
            pop_change_thousands = pop_change / 1000  # 천 단위

            # 인구 변화율 계산 (%)
            pop_pct_change = ((pop_end['인구'] - pop_start['인구']) / pop_start['인구'] * 100).sort_values(ascending=False)

            # 지역명 영어 번역 (예시)
            kor_to_eng = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }

            # 인구 변화량 그래프
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            sns.barplot(x=pop_change_thousands.values, y=[kor_to_eng.get(r, r) for r in pop_change_thousands.index], 
                        ax=ax1, palette="viridis")
            ax1.set_xlabel("Population Change (Thousands)")
            ax1.set_ylabel("Region")
            ax1.set_title("Population Change Over Last 5 Years")

            # 막대값 표시
            for i, v in enumerate(pop_change_thousands.values):
                ax1.text(v + 0.1, i, f"{v:.1f}", color='black', va='center')

            st.pyplot(fig1)

            # 인구 변화율 그래프
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            sns.barplot(x=pop_pct_change.values, y=[kor_to_eng.get(r, r) for r in pop_pct_change.index], 
                        ax=ax2, palette="magma")
            ax2.set_xlabel("Population Change Rate (%)")
            ax2.set_ylabel("Region")
            ax2.set_title("Population Change Rate Over Last 5 Years")

            # 막대값 표시
            for i, v in enumerate(pop_pct_change.values):
                ax2.text(v + 0.3, i, f"{v:.1f}%", color='black', va='center')

            st.pyplot(fig2)

            # 해설
            st.markdown("""
            - The first chart shows the absolute population change (in thousands) for each region over the last 5 years.
            - Regions with positive values indicate population growth, while negative values indicate decline.
            - The second chart shows the percentage change over the same period, which provides a relative view of growth or decline.
            - Seoul and Gyeonggi typically show significant increases, while some rural regions may experience population decreases.
            """)

        # 4. 변화량 분석
        with tabs[3]:
            st.header("Top 100 Population Changes by Region and Year")

            df_diff = df[df['지역'] != '전국'].copy()
            df_diff = df_diff.sort_values(['지역', '연도'])
            df_diff['인구_증감'] = df_diff.groupby('지역')['인구'].diff()  # 연도별 인구 증감 계산

            # 상위 100개 증감 (절대값 기준 큰 순서)
            df_top100 = df_diff.dropna(subset=['인구_증감']).copy()
            df_top100['abs_change'] = df_top100['인구_증감'].abs()
            df_top100 = df_top100.sort_values('abs_change', ascending=False).head(100)

            # 천단위 콤마 포맷 함수
            def format_thousands(x):
                if pd.isna(x):
                    return ""
                return f"{int(x):,}"

            df_top100_display = df_top100[['지역', '연도', '인구_증감']].copy()
            df_top100_display['인구_증감'] = df_top100_display['인구_증감'].apply(format_thousands)

            # 컬러맵 함수 (증가: 파랑, 감소: 빨강)
            def color_change(val):
                try:
                    val_num = int(val.replace(',', ''))
                except:
                    return ''
                color = ''
                if val_num > 0:
                    color = f'background-color: rgba(0, 0, 255, {min(val_num/100000, 1):.2f}); color: white;'
                elif val_num < 0:
                    color = f'background-color: rgba(255, 0, 0, {min(abs(val_num)/100000, 1):.2f}); color: white;'
                return color

            # 스타일링 적용
            styled_df = df_top100_display.style.applymap(color_change, subset=['인구_증감'])

            st.dataframe(styled_df, use_container_width=True)

        # 5. 시각화
        with tabs[4]:
            st.header("Population Heatmap and Stacked Area Chart by Region and Year")

            # 지역명 한글 → 영어 매핑 (예시, 필요시 더 추가)
            region_map = {
                '서울': 'Seoul',
                '부산': 'Busan',
                '대구': 'Daegu',
                '인천': 'Incheon',
                '광주': 'Gwangju',
                '대전': 'Daejeon',
                '울산': 'Ulsan',
                '세종': 'Sejong',
                '경기': 'Gyeonggi',
                '강원': 'Gangwon',
                '충북': 'Chungbuk',
                '충남': 'Chungnam',
                '전북': 'Jeonbuk',
                '전남': 'Jeonnam',
                '경북': 'Gyeongbuk',
                '경남': 'Gyeongnam',
                '제주': 'Jeju',
                '전국': 'Nationwide'
            }

            df_viz = df.copy()
            df_viz['Region'] = df_viz['지역'].map(region_map)
            df_viz = df_viz.dropna(subset=['Region'])

            # 피벗 테이블 생성: 행=Region, 열=Year, 값=Population
            pivot_df = df_viz.pivot(index='Region', columns='연도', values='인구').fillna(0)

            import matplotlib.pyplot as plt
            import seaborn as sns

            # 히트맵 (지역 x 연도 인구수)
            plt.figure(figsize=(12, 8))
            sns.heatmap(pivot_df, cmap='YlGnBu', linewidths=0.5, linecolor='gray')
            plt.title('Population Heatmap by Region and Year')
            plt.xlabel('Year')
            plt.ylabel('Region')
            st.pyplot(plt.gcf())
            plt.clf()

            # 누적 영역 그래프
            plt.figure(figsize=(14, 7))
            pivot_df.T.plot.area(colormap='tab20', alpha=0.8)
            plt.title('Stacked Area Chart of Population by Region and Year')
            plt.xlabel('Year')
            plt.ylabel('Population')
            plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
            plt.tight_layout()
            st.pyplot(plt.gcf())
            plt.clf()



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