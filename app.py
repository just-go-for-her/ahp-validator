import streamlit as st
import google.generativeai as genai

# --------------------------------------------------------------------------
# 1. 설정 및 API 키 입력 (가장 안전한 사이드바 방식)
# --------------------------------------------------------------------------
st.set_page_config(page_title="AHP 전문 논리 진단기", page_icon="⚖️", layout="wide")

with st.sidebar:
    st.header("🔐 인증 설정")
    api_key = st.text_input(
        "Google API Key", 
        type="password",
        placeholder="AIzaSy... 키를 입력하세요",
        help="Google AI Studio에서 발급받은 키를 입력하세요."
    )
    st.info("💡 **진단 기준**\n1. 독립성 위반 (인과관계)\n2. MECE (중복/누락)\n3. 가중치 희석 (개수 불균형)")

# Gemini 설정
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"키 설정 오류: {e}")

# --------------------------------------------------------------------------
# 2. AI 분석 함수 (작성자님의 AHP 이론 반영)
# --------------------------------------------------------------------------
def analyze_ahp_logic(goal, parent, children):
    if not children:
        return {"text": "⚠️ 하위 항목이 없습니다."}
    
    # [핵심] 작성자님이 주신 AHP 이론을 프롬프트에 주입
    prompt = f"""
    당신은 AHP(계층화 분석법) 방법론 전문가입니다. 
    아래 [분석 대상]이 [진단 기준]을 위반하는지 냉철하게 평가하세요.

    [분석 대상]
    - 최종목표: {goal}
    - 상위기준: {parent}
    - 하위요소들: {children} (총 {len(children)}개)

    [진단 기준]
    1. **구조적 독립성 위반 (Independence)**: 
       - 항목끼리 인과관계(원인-결과)가 있으면 안 됩니다. (예: 안전성 vs 에어백 개수 -> 오류)
       - 항목 간 상관관계가 너무 높으면 지적하세요.
    2. **MECE 원칙 (상호배타, 전체포괄)**:
       - 개념이 겹치면 안 됩니다. (예: 직원역량 vs 업무수행능력 -> 중복)
       - 상위 기준을 설명하는 데 치명적으로 누락된 요소가 있으면 지적하세요.
    3. **가중치 희석 및 인지 부하 (Rule of 7)**:
       - 하위 요소가 7개를 초과하면 '인지 과부하' 및 '가중치 희석' 위험으로 경고하세요.
       - 너무 적거나(1개) 너무 많으면 계층 재조정(Sub-cluster)을 제안하세요.

    [출력 양식] - 서술형 금지, 아래 항목만 짧게 출력
    등급: [양호 / 주의 / 위험] 중 하나
    핵심진단: (진단 기준에 근거하여 20자 이내 요약)
    독립성/MECE: (위반 사항이 있으면 구체적으로, 없으면 '통과')
    제안: (수정 방향이나 항목 병합/분할 제안)
    """
    
    try:
        response = model.generate_content(prompt)
        return {"text": response.text}
    except Exception as e:
        return {"text": f"통신 오류: {e}"}

# --------------------------------------------------------------------------
# 3. 세션 상태 초기화
# --------------------------------------------------------------------------
if 'main_count' not in st.session_state: st.session_state.main_count = 1 
if 'sub_counts' not in st.session_state: st.session_state.sub_counts = {}

# --------------------------------------------------------------------------
# 4. 메인 화면 UI
# --------------------------------------------------------------------------
st.title("⚖️ AHP 구조 논리 정밀 진단기")
st.caption("독립성 위반, MECE 결여, 가중치 희석 현상을 중점적으로 분석합니다.")
st.divider()

if not api_key:
    st.warning("👈 왼쪽 사이드바에 API Key를 먼저 입력해주세요.")
    st.stop()

# [Step 1] 목표 및 1차 기준
col_goal, _ = st.columns([2, 1])
with col_goal:
    goal = st.text_input("🎯 1. 최종 목표", placeholder="예: 차세대 국방 AI 시스템 도입")

if goal:
    st.subheader("2. 1차 기준 설정")
    main_criteria = []
    for i in range(st.session_state.main_count):
        val = st.text_input(f"기준 {i+1}", key=f"main_{i}", placeholder="기준 항목 입력")
        if val: main_criteria.append(val)
    
    if st.button("➕ 기준 추가"):
        st.session_state.main_count += 1
        st.rerun()

    # [Step 2] 하위 항목 및 진단
    structure_data = {}
    
    if main_criteria:
        st.divider()
        st.subheader("3. 상세 구조 설계 및 진단")
        
        # 전체 1차 기준에 대한 구조적 균형 체크 (가중치 희석 방지)
        if len(main_criteria) > 7:
             st.warning(f"⚠️ 1차 기준이 {len(main_criteria)}개입니다. 7±2 원칙을 초과하여 쌍대비교 시 일관성이 떨어질 수 있습니다.")
        
        for criterion in main_criteria:
            with st.expander(f"📂 '{criterion}' 하위 요소 구성", expanded=True):
                # 항목 관리
                if criterion not in st.session_state.sub_counts:
                    st.session_state.sub_counts[criterion] = 1
                
                sub_items = []
                for j in range(st.session_state.sub_counts[criterion]):
                    s_val = st.text_input(f"ㄴ {criterion} 세부항목 {j+1}", key=f"sub_{criterion}_{j}")
                    if s_val: sub_items.append(s_val)
                
                col_btn, _ = st.columns([1, 4])
                if col_btn.button(f"➕ 항목 추가", key=f"btn_{criterion}"):
                    st.session_state.sub_counts[criterion] += 1
                    st.rerun()
                
                structure_data[criterion] = sub_items

        st.divider()
        st.header("4. 전문가 진단 결과")
        
        if st.button("🚀 정밀 분석 시작", type="primary", use_container_width=True):
            with st.spinner("논리적 오류(독립성, MECE, 희석효과)를 검사 중입니다..."):
                
                # 1. 1차 기준 자체 진단
                res_main = analyze_ahp_logic(goal, goal, main_criteria)
                st.markdown(f"### 🚩 1차 기준 ({len(main_criteria)}개) 평가")
                st.info(res_main['text'])
                
                st.markdown("---")
                
                # 2. 세부 항목 진단
                st.markdown("### 🔍 세부 항목 평가")
                for parent, children in structure_data.items():
                    # 파이썬 레벨에서의 개수 경고 (작성자님의 가이드라인 반영)
                    count_warning = ""
                    if len(children) >= 8:
                        count_warning = f"⚠️ **[개수 경고]** 하위 항목이 {len(children)}개입니다. 유사한 항목끼리 묶어 중간 계층(Sub-cluster)을 만드는 것을 권장합니다."
                    elif len(children) == 1:
                        count_warning = "⚠️ **[개수 주의]** 하위 항목이 1개뿐입니다. 상위 기준과 의미가 동일하여 가중치 계산이 무의미할 수 있습니다."

                    # AI 진단 호출
                    res = analyze_ahp_logic(goal, parent, children)
                    text_res = res.get("text", "")
                    
                    # 카드 색상 결정
                    if "위험" in text_res:
                        color, icon = "#ff4b4b", "🚨"
                    elif "주의" in text_res:
                        color, icon = "#ffa421", "⚠️"
                    else:
                        color, icon = "#21c354", "✅"

                    # 결과 출력
                    with st.container():
                        st.markdown(f"""
                        <div style="border: 2px solid {color}; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                            <h4 style="margin:0;">{icon} <b>'{parent}'</b> 진단</h4>
                            {f'<p style="color:red; font-weight:bold;">{count_warning}</p>' if count_warning else ''}
                            <div style="margin-top: 10px; white-space: pre-line;">
                                {text_res}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
