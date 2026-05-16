import streamlit as st
import datetime 
import pandas as pd 
import calendar

# 페이지 넓게 쓰기 설정
st.set_page_config(layout="wide")

st.title("🏠 한국주택금융공사 3대 상환방식 실시간 비교 대시보드")
st.markdown("---")

# ==============================================================================
# [배경 로직] 3대 상환방식 핵심 엔진 함수 정의
# ==============================================================================

def equal_pay_hf(loan_amount, loan_years, interest_rate):
    total_months = loan_years * 12 
    monthly_rate = interest_rate / 12
    monthly_pmt = loan_amount * (monthly_rate * (1+monthly_rate)**total_months) / ((1+monthly_rate)**total_months - 1)
    fixed_pmt = int(monthly_pmt)

    balance = loan_amount 
    cumulative_principal, cumulative_interest = 0, 0
    schedule_data = [] 
    start_date = datetime.date.today()
    last_payment_date = start_date

    for i in range(1, total_months + 1):
        payment_date = (start_date + pd.DateOffset(months=i)).date()
        
        if balance <= 0:
            schedule_data.append({
                '회차': i, '상환예정일자': payment_date.strftime('%Y-%m-%d'),
                '원리금': 0, '원금': 0, '이자': 0,
                '이자상환누계': cumulative_interest, '납입원금누계': cumulative_principal
            })
            continue

        interest_payment_exact = 0.0 
        current_date = last_payment_date
        while current_date < payment_date:
            days_in_year = 366 if calendar.isleap(current_date.year) else 365
            interest_payment_exact += balance * interest_rate * (1 / days_in_year)
            current_date += datetime.timedelta(days=1)
            
        interest_payment = int(interest_payment_exact)
        principal_payment = fixed_pmt - interest_payment 

        if principal_payment >= balance or i == total_months:
            principal_payment = int(balance)
            fixed_pmt = principal_payment + interest_payment

        balance -= principal_payment
        cumulative_principal += principal_payment
        cumulative_interest += interest_payment

        schedule_data.append({
            '회차': i, '상환예정일자': payment_date.strftime('%Y-%m-%d'),
            '원리금': fixed_pmt, '원금': principal_payment, '이자': interest_payment,
            '이자상환누계': cumulative_interest, '납입원금누계': cumulative_principal
        })
        last_payment_date = current_date
                
    return pd.DataFrame(schedule_data)

def equal_principal_hf(loan_amount, loan_years, interest_rate):
    total_months = loan_years * 12 
    fixed_principal = int(loan_amount / total_months)
    balance = float(loan_amount)
    sum_principal, sum_interest = 0, 0
    schedule_data = [] 
    start_date = datetime.date.today()
    last_payment_date = start_date

    for i in range(1, total_months + 1):
        payment_date = (start_date + pd.DateOffset(months=i)).date()
        
        if balance <= 0:
            schedule_data.append({
                '회차': i, '상환예정일자': payment_date.strftime('%Y-%m-%d'),
                '원리금': 0, '원금': 0, '이자': 0,
                '이자상환누계': int(sum_interest), '납입원금누계': int(sum_principal)
            })
            continue

        interest_payment_exact = 0.0 
        current_date = last_payment_date
        while current_date < payment_date:
            days_in_year = 366 if calendar.isleap(current_date.year) else 365
            interest_payment_exact += balance * interest_rate * (1.0 / days_in_year)
            current_date += datetime.timedelta(days=1)
            
        interest_payment = int(interest_payment_exact)
        principal_payment = fixed_principal
        
        if principal_payment >= balance or i == total_months:
            principal_payment = int(balance)
            
        monthly_pmt = principal_payment + interest_payment

        balance -= principal_payment
        sum_principal += principal_payment
        sum_interest += interest_payment

        schedule_data.append({
            '회차': i, '상환예정일자': payment_date.strftime('%Y-%m-%d'),
            '원리금': int(monthly_pmt), '원금': int(principal_payment), '이자': int(interest_payment),
            '이자상환누계': int(sum_interest), '납입원금누계': int(sum_principal)
        })
        last_payment_date = payment_date
                
    return pd.DataFrame(schedule_data)

def graduated_payment_hf(loan_amount, loan_years, interest_rate):
    total_months = min(loan_years * 12, 480) 
    monthly_increment = int(loan_amount * 0.0000037125) 
    first_pmt = int(loan_amount * (1_613_698 / 400_000_000)) 
    balance = float(loan_amount)
    sum_principal, sum_interest = 0, 0
    schedule_data = [] 
    start_date = datetime.date.today()
    last_payment_date = start_date

    for i in range(1, total_months + 1):
        payment_date = (start_date + pd.DateOffset(months=i)).date()
        
        if balance <= 0:
            schedule_data.append({
                '회차': i, '상환예정일자': payment_date.strftime('%Y-%m-%d'),
                '원리금': 0, '원금': 0, '이자': 0,
                '이자상환누계': int(sum_interest), '납입원금누계': int(sum_principal)
            })
            continue

        interest_payment_exact = 0.0 
        current_date = last_payment_date
        while current_date < payment_date:
            days_in_year = 366 if calendar.isleap(current_date.year) else 365
            interest_payment_exact += balance * interest_rate * (1.0 / days_in_year)
            current_date += datetime.timedelta(days=1)
            
        interest_payment = int(interest_payment_exact)
        current_fixed_pmt = first_pmt + (i - 1) * monthly_increment
        principal_payment = current_fixed_pmt - interest_payment
        
        if principal_payment < 0: 
            principal_payment = 0

        if principal_payment >= balance or i == total_months:
            principal_payment = int(balance)
            current_fixed_pmt = principal_payment + interest_payment

        balance -= principal_payment
        sum_principal += principal_payment
        sum_interest += interest_payment

        schedule_data.append({
            '회차': i, '상환예정일자': payment_date.strftime('%Y-%m-%d'),
            '원리금': int(current_fixed_pmt), '원금': int(principal_payment), '이자': int(interest_payment),
            '이자상환누계': int(sum_interest), '납입원금누계': int(sum_principal)
        })
        last_payment_date = payment_date
                
    return pd.DataFrame(schedule_data)

def process_display_df(df, is_summary=True):
    df_display = df.copy()
    
    def get_period_name(row_idx):
        if is_summary:
            if row_idx <= 11: return f"{row_idx}달"
            else: return f"{row_idx // 12}년"
        else:
            if row_idx <= 11: return f"{row_idx}개월 차"
            else:
                years = row_idx // 12
                months = row_idx % 12
                return f"{years}년 0개월 차" if months == 0 else f"{years}년 {months}개월 차"
            
    df_display['경과기간'] = df_display['회차'].apply(get_period_name)
    cols = ['경과기간', '상환예정일자', '원리금', '원금', '이자', '이자상환누계', '납입원금누계']
    df_display = df_display[cols]
    
    if is_summary:
        target_indices = list(range(1, 12)) + [y * 12 for y in [1, 2, 3, 4, 5, 10, 20, 30, 40, 50]]
        df_display = df_display[df['회차'].isin(target_indices)].reset_index(drop=True)
        
    amt_cols = ['원리금', '원금', '이자', '이자상환누계', '납입원금누계']
    for c in amt_cols:
        df_display[c] = df_display[c].apply(lambda x: f"{x:,}")
        
    return df_display


# ==============================================================================
# [UI 구현부] 1. 상단 인풋 영역
# ==============================================================================
col1, col2, col3, col4 = st.columns(4)
with col1:
    house_price = st.number_input("주택 가격 (원)", value=600_000_000, step=10_000_000)
with col2:
    my_cash = st.number_input("내가 가진 돈 (원)", value=200_000_000, step=10_000_000)
with col3:
    input_rate = st.number_input("입력 금리 (%)", value=4.8, step=0.05, min_value=0.1)
with col4:
    loan_year = st.selectbox("대출 기간 (년)", [10, 20, 30, 40, 50], index=4)

calculated_loan = house_price - my_cash

if calculated_loan <= 0:
    st.error("보유 자금이 주택 가격보다 많거나 같습니다. 대출이 필요 없습니다.")
else:
    st.info(f"💰 **자동 계산된 대출 신청 금액:** {calculated_loan:,}원 (약 {calculated_loan // 100_000_000}억 {(calculated_loan % 100_000_000) // 10_000}만 원)")
    
    # 인풋 칸 밑에 실시간 주의사항 경고 박스 노출
    with st.expander("⚠️ 대출 시뮬레이션 관련 필수 주의사항 (클릭하여 확인)", expanded=True):
        st.markdown(f"""
        *   **정산 오차 안내:** 주택금융공사 공식 결과와 매월 미세한 정산 차이가 발생할 수 있습니다.
        *   **체증식 만기 제한 규정:** 현재 선택하신 대출 기간은 **{loan_year}년**입니다. 한국주택금융공사 규정에 따라 체증식 상환 방식을 선택할 경우, 대출 기간을 50년으로 설정하더라도 **최대 40년(480개월) 만기가 강제 적용**됩니다.
        """)
    st.markdown("---")

    # 금리 분기 설정
    rate_raw = input_rate * 0.01
    if loan_year == 50:
        rate_graduated = (input_rate - 0.05) * 0.01
        graduated_label = f"{input_rate - 0.05:.2f}% (-0.05% 기간 보정 우대)"
    else:
        rate_graduated = input_rate * 0.01
        graduated_label = f"{input_rate:.2f}% (원본 금리 동일 적용)"
    
    # 3대 상환방식 연산 가동
    df_equal_principal_full = equal_principal_hf(calculated_loan, loan_year, rate_raw)
    df_equal_pay_full = equal_pay_hf(calculated_loan, loan_year, rate_raw)
    df_graduated_full = graduated_payment_hf(calculated_loan, loan_year, rate_graduated)

    # 마이너스 제외 순수 진행분 통계 추출
    df_eq_p_active = df_equal_principal_full[df_equal_principal_full['원리금'] > 0]
    df_eq_pay_active = df_equal_pay_full[df_equal_pay_full['원리금'] > 0]
    df_grad_active = df_graduated_full[df_graduated_full['원리금'] > 0]

    eq_p_min, eq_p_max = df_eq_p_active['원리금'].min(), df_eq_p_active['원리금'].max()
    eq_p_total_int = df_equal_principal_full['이자'].sum()

    eq_pay_min, eq_pay_max = df_eq_pay_active['원리금'].min(), df_eq_pay_active['원리금'].max()
    eq_pay_total_int = df_equal_pay_full['이자'].sum()

    grad_min, grad_max = df_grad_active['원리금'].min(), df_grad_active['원리금'].max()
    grad_total_int = df_graduated_full['이자'].sum()

    # ==============================================================================
    # 💡 [요구사항 1] DTI 연동을 위한 본인의 연봉 입력 컴포넌트 추가 배치
    # ==============================================================================
    st.subheader("📊 대출 규제 비율 및 기본 지표 (LTV / 실시간 DTI)")
    
    # 사용자 연봉 인풋창 개설 (기본값 5천만 원 설정)
    user_annual_income = st.number_input("💵 본인의 세전 연봉(연소득)을 입력하세요 (원)", value=50_000_000, step=5_000_000)
    st.caption(f"✍️ 입력된 연소득: **{user_annual_income:,}원** ({user_annual_income // 10_000:,}만 원)")
    # 1년 차(1~12회차) 각 방식별 총 원리금 상환액 집계
    eq_p_1st_year_pmt = df_equal_principal_full.iloc[:12]['원리금'].sum()
    eq_pay_1st_year_pmt = df_equal_pay_full.iloc[:12]['원리금'].sum()
    grad_1st_year_pmt = df_graduated_full.iloc[:12]['원리금'].sum()

    # 실시간 DTI 계산 공식 대입
    if user_annual_income > 0:
        dti_eq_p = (eq_p_1st_year_pmt / user_annual_income) * 100
        dti_eq_pay = (eq_pay_1st_year_pmt / user_annual_income) * 100
        dti_grad = (grad_1st_year_pmt / user_annual_income) * 100
    else:
        dti_eq_p = dti_eq_pay = dti_grad = 0.0

    ltv_value = (calculated_loan / house_price) * 100
    
    ltv_col, dti_col = st.columns(2)
    with ltv_col:
        st.metric(label="현재 대출의 LTV (주택담보대출비율)", value=f"{ltv_value:.2f} %")
        if ltv_value > 80:
            st.error("⚠️ 규제 가이드(일반 80%)를 초과하는 수준입니다. 대출 한도를 재점검하세요.")
        elif 70 <= ltv_value <= 80:
            st.warning("🔶 본인의 LTV 적용범위 내에 드는지 확인하세요 (생애최초, 지역별 규제 등)")
        else:
            st.success("✅ 규제 범위 내 안전한 한도 수준입니다.")
            
    with dti_col:
        st.markdown("**🔍 각 상환방식별 1년 차 기준 실시간 DTI 결과**")
        
        # 3가지 방식의 DTI 가독성 카드 출력
        st.write(f"1. **체감식 (원금균등) :** `{dti_eq_p:.2f}%` (첫해 연간 상환액: {eq_p_1st_year_pmt:,}원)")
        st.write(f"2. **원리금균등 :** `{dti_eq_pay:.2f}%` (첫해 연간 상환액: {eq_pay_1st_year_pmt:,}원)")
        st.write(f"3. **체증식 :** `{dti_grad:.2f}%` (첫해 연간 상환액: {grad_1st_year_pmt:,}원)")
        
        # DTI 통합 규제 모니터링 경고창 (보통 규제선 60% 기준)
        max_current_dti = max(dti_eq_p, dti_eq_pay, dti_grad)
        if max_current_dti > 60:
            st.error("⚠️ DTI 규제선(일반 60%)을 초과하는 방식이 존재합니다. 소득 대비 대출 규모가 과도할 수 있습니다.")
        elif 50 <= max_current_dti <= 60:
            st.warning("🔶 DTI가 한계치(50%~60%)에 근접했습니다. 대출 실행 가능 여부를 금융기관에 확인하세요.")
        else:
            st.success("✅ 세 방식 모두 DTI 규제선 기준 안정권에 속합니다.")
        
    st.markdown("---")

    # 대시보드 메인 일괄 비교 표
    st.subheader("📊 3대 상환방식 원리금 범위 및 총이자 일괄 비교")
    summary_matrix = {
        "상환 방식": ["1. 체감식 (원금균등)", "2. 원리금균등", "3. 체증식 (최대 40년 제한)"],
        "적용 금리": [f"{input_rate}%", f"{input_rate}%", graduated_label],
        "최소 월납입금": [f"{eq_p_min:,}원", f"{eq_pay_min:,}원", f"{grad_min:,}원"],
        "최대 월납입금": [f"{eq_p_max:,}원", f"{eq_pay_max:,}원", f"{grad_max:,}원"],
        "최종 지출 총 이자": [f"{eq_p_total_int:,}원", f"{eq_pay_total_int:,}원", f"{grad_total_int:,}원"]
    }
    st.table(pd.DataFrame(summary_matrix))
    st.markdown("---")

    # ==============================================================================
    # 하단 개별 방식 대시보드 표 레이아웃
    # ==============================================================================

    # 📌 섹션 ①: 체감식 상환 방식
    st.subheader("1. 원금균등 분할상환 방식 (체감식)")
    st.markdown(f"💡 **월납입금 범위:** {eq_p_max:,}원 ~ {eq_p_min:,}원 | 🎯 **최종 지출 총 이자합계:** `{eq_p_total_int:,}원`")
    show_all_1 = st.checkbox("🔄 1회차부터 매 회차별 전체 상세 보기 (X년 X개월 차 표시)", key="show_1")
    st.dataframe(process_display_df(df_equal_principal_full, is_summary=not show_all_1), use_container_width=True)
    st.markdown("---")

    # 📌 섹션 ②: 원리금균등 상환 방식
    st.subheader("2. 원리금균등 분할상환 방식")
    st.markdown(f"💡 **월납입금 범위:** {eq_pay_max:,}원 ~ {eq_pay_min:,}원 | 🎯 **최종 지출 총 이자합계:** `{eq_pay_total_int:,}원`")
    show_all_2 = st.checkbox("🔄 1회차부터 매 회차별 전체 상세 보기 (X년 X개월 차 표시)", key="show_2")
    st.dataframe(process_display_df(df_equal_pay_full, is_summary=not show_all_2), use_container_width=True)
    st.markdown("---")

    # 📌 섹션 ③: 체증식 상환 방식
    st.subheader(f"3. 체증식 분할상환 방식 (적용 만기: {min(loan_year, 40)}년)")
    st.markdown(f"💡 **월납입금 범위:** {grad_min:,}원 ~ {grad_max:,}원 | 🎯 **최종 지출 총 이자합계:** `{grad_total_int:,}원`")
    show_all_3 = st.checkbox("🔄 1회차부터 매 회차별 전체 상세 보기 (X년 X개월 차 표시)", key="show_3")
    st.dataframe(process_display_df(df_graduated_full, is_summary=not show_all_3), use_container_width=True)