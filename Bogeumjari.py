import streamlit as st
import datetime 
import pandas as pd 
import calendar
from dateutil.relativedelta import relativedelta

# 페이지 넓게 쓰기 설정
st.set_page_config(layout="wide")

# 💡 [요구사항 1] 제목 변경
st.title("🏠 한국주택금융공사 3대 상환방식 비교 대시보드")
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
# [UI 구현부] 1. 상단 기본 대출 조건 인풋 영역
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
    
    # 필수 주의사항 안내 박스
    with st.expander("⚠️ 대출 시뮬레이션 관련 필수 주의사항", expanded=True):
        st.markdown(f"""
        *   **정산 오차 안내:** 주택금융공사 공식 결과와 매월 미세한 정산 차이가 발생할 수 있습니다.
        *   **체증식 만기 제한 규정:** 현재 선택하신 대출 기간은 **{loan_year}년**입니다. 한국주택금융공사 규정에 따라 체증식 상환 방식을 선택할 경우, 대출 기간을 50년으로 설정하더라도 **최대 40년(480개월) 만기가 강제 적용**됩니다.
        """)
    st.markdown("---")

# ==============================================================================
    # 2. 소득 증빙 방식 설정 영역 (일반 vs 1년 미만 소급적용)
    # ==============================================================================
    st.subheader("👥 소득 증빙 방식 설정")
    is_under_one_year = st.checkbox("🏃‍♂️ 현재 입사 1년 미만 근로자이신가요? (소급 연환산 및 90% 인정 적용)")

    if is_under_one_year:
        # 3컬럼에서 미래 날짜 조절을 위해 2줄 레이아웃으로 변경
        col_entry, col_target_date = st.columns(2)
        with col_entry:
            entry_date = st.date_input("회사 입사일 선택", value=datetime.date(2025, 10, 13))
        with col_target_date:
            # 💡 [핵심 추가] 미래의 대출 신청 예정일을 선택하는 칸 (기본값은 오늘)
            target_loan_date = st.date_input("📅 대출 신청 예정일을 선택하세요", value=datetime.date.today())
            
            if target_loan_date < entry_date:
                st.error("대출 신청일은 입사일보다 빠를 수 없습니다.")
                target_loan_date = datetime.date.today()

        # 💡 오늘이 아닌 '내가 고른 미래 신청일' 기준으로 재직 개월 수를 자동 역산!
        delta = relativedelta(target_loan_date, entry_date)
        working_months = round(delta.years * 12 + delta.months + (delta.days / 30.4), 1)
        
        # 1개월 미만 극초기 예외처리 가드
        if working_months < 1.0:
            working_months = 1.0
            
        st.warning(f"🎯 선택하신 대출 신청일({target_loan_date.strftime('%Y-%m-%d')}) 기준 예상 재직 기간은 **{delta.years}년 {delta.months}개월 {delta.days}일** (연환산 분모: **{working_months}개월**) 입니다.")

        col_salary_input, col_bonus_input = st.columns(2)
        with col_salary_input:
            total_base_salary = st.number_input("💰 [신청일 기준] 누적 접수될 '세전 월급 합계' (원)", value=24_000_000, step=1_000_000)
            st.caption(f"✍️ 신청 시점까지 받게 될 총 월급 누계: **{total_base_salary:,}원**")
        with col_bonus_input:
            total_bonus = st.number_input("🎁 [신청일 기준] 누적 접수될 '세전 상여금/성과급 총합' (원)", value=5_000_000, step=500_000)
            st.caption(f"✍️ 신청 시점까지 받게 될 총 상여 누계: **{total_bonus:,}원**")
            
        # 90% 소득인정 보정 수식 가동
        raw_annual_income = ((total_base_salary / working_months) * 12) + total_bonus
        user_annual_income = int(raw_annual_income * 0.90)  # 90% 소득인정 가드 적용
            
        st.success(f"🎯 **선택하신 신청일 기준 소급 인정 연봉 (90% 적용):** **{user_annual_income:,}원**")
        st.caption("⚠️ **주의사항:** 주택금융공사 지침에 의거, 1년 미만 재직자의 연환산 소득은 소득 과대평가 방지를 위해 산출 금액의 **90%만 최종 상환 능력 소득으로 인정**합니다.")
    else:
        user_annual_income = st.number_input("💵 본인의 세전 연봉(연소득)을 입력하세요 (원)", value=50_000_000, step=5_000_000)
        st.caption(f"✍️ 입력된 연소득: **{user_annual_income:,}원** ({user_annual_income // 10_000:,}만 원)")
    st.markdown("---")

    # 금리 분기 설정
    rate_raw = input_rate * 0.01
    if loan_year == 50:
        rate_graduated = (input_rate - 0.05) * 0.01
        graduated_label = f"{input_rate - 0.05:.2f}% (-0.05% 기간 보정)"
    else:
        rate_graduated = input_rate * 0.01
        graduated_label = f"{input_rate:.2f}% (원본 금리 동일 적용)"
    
    # 3대 상환방식 연산 가동
    df_equal_principal_full = equal_principal_hf(calculated_loan, loan_year, rate_raw)
    df_equal_pay_full = equal_pay_hf(calculated_loan, loan_year, rate_raw)
    df_graduated_full = graduated_payment_hf(calculated_loan, loan_year, rate_graduated)

    # 통계 추출
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
    # 💡 [요구사항 7] 매 칸마다 접을 수 있는 Expander(접기 화살표) 블록화 도입
    # ==============================================================================

    # 📦 접기 칸 1: 규제 비율 및 실시간 DTI
    with st.expander("📊 섹션 A. 대출 규제 비율 및 기본 지표 (LTV / 실시간 DTI)", expanded=True):
        eq_p_1st_year_pmt = df_equal_principal_full.iloc[:12]['원리금'].sum()
        eq_pay_1st_year_pmt = df_equal_pay_full.iloc[:12]['원리금'].sum()
        grad_1st_year_pmt = df_graduated_full.iloc[:12]['원리금'].sum()

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
            if ltv_value > 80: st.error("⚠️ 규제 가이드(일반 80%)를 초과하는 수준입니다. 대출 한도를 재점검하세요.")
            elif 70 <= ltv_value <= 80: st.warning("🔶 본인의 LTV 적용범위 내에 드는지 확인하세요 (생애최초, 지역별 규제 등)")
            else: st.success("✅ 규제 범위 내 안전한 한도 수준입니다.")
                
        with dti_col:
            st.markdown("**🔍 인정 연봉 기준 실시간 DTI 계산 결과**")
            st.write(f"1. **체감식 (원금균등) :** `{dti_eq_p:.2f}%` (첫해 연간 상환액: {eq_p_1st_year_pmt:,}원)")
            st.write(f"2. **원리금 균등분할 방식 :** `{dti_eq_pay:.2f}%` (첫해 연간 상환액: {eq_pay_1st_year_pmt:,}원)")
            st.write(f"3. **체증식 :** `{dti_grad:.2f}%` (첫해 연간 상환액: {grad_1st_year_pmt:,}원)")

    # 📦 접기 칸 2: 소득 기반 한도 역산 리포트
    with st.expander("📐 섹션 B. 나의 소득 기반 최대 대출 한도 가능선", expanded=True):
        if user_annual_income > 0:
            max_monthly_allowed = (user_annual_income * 0.60) / 12
            total_m = loan_year * 12
            m_rate = (input_rate * 0.01) / 12
            if m_rate > 0:
                df_factor = ((1 + m_rate) ** total_m - 1) / (m_rate * (1 + m_rate) ** total_m)
                dti_max_principal = int((max_monthly_allowed * df_factor) // 10_000) * 10_000
            else:
                dti_max_principal = int((max_monthly_allowed * total_m) // 10_000) * 10_000
                
            final_max_possible = min(dti_max_principal, 500_000_000)
            st.markdown(f"📊 입력하신 연소득 규제 조건 상 **최대 허용 가능한 대출 원금 한도:** 약 **`{final_max_possible:,}원`** (최대 5억 한도 가드 적용)")
            # 💡 [요구사항 6] 주의사항 안내문구 수정
            st.caption("⚠️ **주의사항:** 본 한도는 기타 담보 평가 요소나 생애최초·신혼가구 여부 등을 배제하고 순수 DTI 규제선(60%)만을 대입해 역산한 수치입니다. 실제 정밀한 대출 가능금액은 개인별 우대 요건에 따라 달라질 수 있으므로 반드시 한국주택금융공사 공식 공시내역을 최종 참고하시기 바랍니다.")

    # 📦 접기 칸 3: 3대 상환방식 일괄 비교 표
    with st.expander("📊 섹션 C. 3대 상환방식 원리금 범위 및 총이자 일괄 비교 표", expanded=True):
        summary_matrix = {
            "상환 방식": ["1. 체감식 (원금균등)", "2. 원리금균등", "3. 체증식 (최대 40년 제한)"],
            "적용 금리": [f"{input_rate}%", f"{input_rate}%", graduated_label],
            "최소 월납입금": [f"{eq_p_min:,}원", f"{eq_pay_min:,}원", f"{grad_min:,}원"],
            "최대 월납입금": [f"{eq_p_max:,}원", f"{eq_pay_max:,}원", f"{grad_max:,}원"],
            "최종 지출 총 이자": [f"{eq_p_total_int:,}원", f"{eq_pay_total_int:,}원", f"{grad_total_int:,}원"]
        }
        st.table(pd.DataFrame(summary_matrix))

    # 📦 접기 칸 4: 원금균등 상세 표
    with st.expander("📋 섹션 D. [상세] 1. 체감식 분할상환 방식 스케줄", expanded=False):  # 기본은 접어둠
        st.markdown(f"💡 **월납입금 범위:** {eq_p_max:,}원 ~ {eq_p_min:,}원 | 🎯 **최종 지출 총 이자합계:** `{eq_p_total_int:,}원`")
        show_all_1 = st.checkbox("🔄 1회차부터 매 회차별 전체 상세 보기 ", key="show_1")
        st.dataframe(process_display_df(df_equal_principal_full, is_summary=not show_all_1), use_container_width=True)

    # 📦 접기 칸 5: 원리금균등 상세 표
    with st.expander("📋 섹션 E. [상세] 2. 원리금균등 분할상환 방식 스케줄", expanded=False):
        st.markdown(f"💡 **월납입금 범위:** {eq_pay_max:,}원 ~ {eq_pay_min:,}원 | 🎯 **최종 지출 총 이자합계:** `{eq_pay_total_int:,}원`")
        show_all_2 = st.checkbox("🔄 1회차부터 매 회차별 전체 상세 보기 ", key="show_2")
        st.dataframe(process_display_df(df_equal_pay_full, is_summary=not show_all_2), use_container_width=True)

    # 📦 접기 칸 6: 체증식 상세 표
    with st.expander("📋 섹션 F. [상세] 3. 체증식 분할상환 방식 스케줄", expanded=False):
        st.markdown(f"💡 **월납입금 범위:** {grad_min:,}원 ~ {grad_max:,}원 | 🎯 **최종 지출 총 이자합계:** `{grad_total_int:,}원`")
        show_all_3 = st.checkbox("🔄 1회차부터 매 회차별 전체 상세 보기 ", key="show_3")
        st.dataframe(process_display_df(df_graduated_full, is_summary=not show_all_3), use_container_width=True)