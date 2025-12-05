import streamlit as st
import google.generativeai as genai

# --------------------------------------------------------------------------
# [플랜 B] 키 입력 방식 변경 (Secrets 오류 시 사용)
# --------------------------------------------------------------------------
st.set_page_config(page_title="AI 논리 진단기 Pro", page_icon="🧠", layout="wide")

# 사이드바에서 키를 직접 입력받음 (가장 확실한 방법)
with st.sidebar:
    st.header("🔐 인증 설정")
    api_key = st.text_input(
        "Google API Key", 
        type="password",
        placeholder="AIzaSy... 로 시작하는 키를 입력하세요",
        help="Google AI Studio에서 발급받은 키를 여기에 붙여넣으세요."
    )
    if not api_key:
        st.warning("👈 먼저 이곳에 API 키를 입력해야 작동합니다.")
        st.markdown("[키 발급받기](https://aistudio.google.com/app/apikey)")

# Gemini 설정
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"키 설정 오류: {e}")

# --------------------------------------------------------------------------
# 화면 UI (기능은 동일)
# --------------------------------------------------------------------------
st.title("🧠 AHP 논리 구조 진단기")
st.divider()

if not api_key:
    st.error("👈 왼쪽 사이드바에 API Key를 넣어주세요.")
    st.stop() # 키 없으면 여기서 멈춤

# ... (아래는 기존 로직과 동일) ...

# [Step 1] 목표 설정
col_goal, _ = st.columns([2, 1])
with col_goal:
    goal = st.text_input("🎯 1. 최종 목표는 무엇인가요?", placeholder="예: 차세대 국방 AI 시스템 도입")

if 'main_count' not in st.session_state:
    st.session_state.main_count = 1 
if 'sub_counts' not in st.session_state:
    st.session_state.sub_counts = {}

# 분석 함수
def analyze_structure(goal, parent, children):
    if not children:
        return {"text": "⚠️ 하위 항목이 입력되지 않았습니다."}
    prompt = f"""
    [분석] 목표:{goal}, 상위:{parent}, 하위:{children}
    [요청] 등급(양호/주의/위험), 핵심진단, 문제점, 제안 형식으로 짧게 답변.
    """
    try:
        response = model.generate_content(prompt)
        return {"text": response.text}
    except Exception as e:
        return {"text": f"통신 오류: {e}"}

if goal:
    st.subheader(f"2. '{goal}'의 평가 기준 설정")
    main_criteria = []
    for i in range(st.session_state.main_count):
        val = st.text_input(f"기준 {i+1}", key=f"main_{i}")
        if val: main_criteria.append(val)
    
    if st.button("➕ 1차 기준 추가"):
        st.session_state.main_count += 1
        st.rerun()

    structure_data = {}
    if main_criteria:
        st.subheader("3. 세부 항목 가지치기")
        for criterion in main_criteria:
            with st.expander(f"📂 '{criterion}' 하위 요소", expanded=True):
                if criterion not in st.session_state.sub_counts:
                    st.session_state.sub_counts[criterion] = 1
                
                sub_items = []
                for j in range(st.session_state.sub_counts[criterion]):
                    s_val = st.text_input(f"ㄴ {criterion}-{j+1}", key=f"sub_{criterion}_{j}")
                    if s_val: sub_items.append(s_val)
                
                if st.button(f"➕ 추가", key=f"btn_{criterion}"):
                    st.session_state.sub_counts[criterion] += 1
                    st.rerun()
                structure_data[criterion] = sub_items

        st.divider()
        if st.button("🚀 진단 시작", type="primary", use_container_width=True):
            with st.spinner("AI 분석 중..."):
                for parent, children in structure_data.items():
                    res = analyze_structure(goal, parent, children)
                    st.success(f"**{parent}** 분석 완료")
                    st.write(res['text'])
