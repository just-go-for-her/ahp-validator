import streamlit as st
import google.generativeai as genai
import json

# --- 1. 페이지 설정 ---
st.set_page_config(
    page_title="AHP 구조 설계 및 AI 진단",
    page_icon="🌳",
    layout="wide"
)

# --- 2. 사이드바: API 키 설정 ---
with st.sidebar:
    st.header("⚙️ 설정 (Settings)")
    api_key = st.text_input(
        "Google API Key 입력", 
        type="password",
        help="Google AI Studio에서 발급받은 키를 입력하세요."
    )
    st.info("입력은 직관적으로, 진단은 AI가 수행합니다.")
    st.caption("Combined Version: Visual UI + AI Logic")

# --- 3. Gemini 분석 함수 ---
def ask_gemini_logic(model, goal, parent, children):
    """
    상위 항목(Parent)과 하위 항목들(Children) 간의 논리적 관계를 진단
    """
    if not children:
        return "하위 항목이 없습니다."

    prompt = f"""
    [역할] AHP 의사결정 방법론 전문가
    [분석 목표] '{goal}' 달성을 위한 계층 구조 진단
    
    [현재 구조]
    - 상위 기준: '{parent}'
    - 하위 요소들: {children}
    
    [요청 사항]
    위 구조에 대해 다음 두 가지를 냉철하게 진단하고 짧게 피드백하시오.
    1. **독립성 (Independence)**: 하위 요소끼리 서로 겹치거나 인과관계가 섞여있지 않은가?
    2. **MECE (누락/중복)**: 상위 기준을 설명하기에 충분한가? 혹은 치명적으로 빠진 요소가 있는가?
    
    [출력 형식]
    - ✅ **양호**: 문제 없음 (이유 간략히)
    - 🚨 **수정 필요**: (구체적인 문제점과 수정 제안)
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ AI 통신 오류: {e}"

# --- 4. 메인 화면 ---
st.title("🌳 AHP 구조 설계 & AI 자동 진단")
st.markdown("복잡한 코드는 잊으세요. **빈칸을 채우면 AI가 논리를 검사합니다.**")

st.divider()

# --------------------------------------------------------------------------
# [Step 1] 구조 설계 (UI 입력)
# --------------------------------------------------------------------------
st.header("Step 1. 구조 설계")

goal = st.text_input("1. 최종 목표는 무엇인가요?", placeholder="예: 차세대 국방 AI 시스템 도입", value="")

if goal:
    st.subheader(f"2. '{goal}'의 1차 기준 설정")
    st.caption("가장 중요한 평가 기준 3가지를 입력하세요.")

    col1, col2, col3 = st.columns(3)
    with col1: c1 = st.text_input("기준 A", placeholder="예: 작전효율성")
    with col2: c2 = st.text_input("기준 B", placeholder="예: 비용")
    with col3: c3 = st.text_input("기준 C", placeholder="예: 기술신뢰도")

    criteria_list = [c for c in [c1, c2, c3] if c]

    # 구조 데이터를 저장할 딕셔너리
    structure_data = {}

    if criteria_list:
        st.subheader("3. 세부 항목 가지치기 (Depth 확장)")
        
        for criterion in criteria_list:
            with st.expander(f"➕ '{criterion}'의 하위 요소 입력", expanded=True):
                sub_c1, sub_c2, sub_c3 = st.columns(3)
                s1 = sub_c1.text_input(f"{criterion}-1", key=f"{criterion}_1", placeholder="세부항목 1")
                s2 = sub_c2.text_input(f"{criterion}-2", key=f"{criterion}_2", placeholder="세부항목 2")
                s3 = sub_c3.text_input(f"{criterion}-3", key=f"{criterion}_3", placeholder="세부항목 3")
                
                subs = [s for s in [s1, s2, s3] if s]
                structure_data[criterion] = subs

        # --------------------------------------------------------------------------
        # [Step 2] AI 진단 리포트
        # --------------------------------------------------------------------------
        st.divider()
        st.header("Step 2. AI 논리 진단")

        if st.button("🚀 구조 확정 및 AI 진단 시작", type="primary"):
            if not api_key:
                st.warning("⚠️ 왼쪽 사이드바에 'Google API Key'를 먼저 입력해주세요!")
            else:
                st.success("엔진 가동! 입력된 구조를 분석합니다...")
                
                # Gemini 모델 설정
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash') # 최신 모델 사용

                # 1. 1차 기준 진단 (Goal -> Criteria)
                st.subheader(f"📂 1차 계층 분석: [ {goal} ]")
                
                # 구조적 진단 (개수)
                if len(criteria_list) < 2:
                    st.warning("🟡 기준이 너무 적습니다. 최소 2개 이상 권장합니다.")
                else:
                    st.caption(f"🔵 구조적 상태: {len(criteria_list)}개 항목 (적정)")

                # AI 진단
                with st.spinner("AI가 1차 기준의 논리를 점검 중입니다..."):
                    feedback = ask_gemini_logic(model, goal, goal, criteria_list)
                    st.info(feedback)

                # 2. 2차 세부 항목 진단 (Criteria -> Sub-criteria)
                if structure_data:
                    st.markdown("---")
                    st.subheader("📂 2차 세부 계층 분석")
                    
                    for parent, children in structure_data.items():
                        with st.expander(f"🔍 '{parent}' 하위 논리 점검", expanded=True):
                            if not children:
                                st.error(f"⚠️ '{parent}'의 하위 항목이 비어있습니다.")
                            else:
                                with st.spinner(f"'{parent}' 분석 중..."):
                                    sub_feedback = ask_gemini_logic(model, goal, parent, children)
                                    st.write(sub_feedback)
                
                st.balloons()
                st.success("모든 분석이 완료되었습니다. 수정이 필요하면 위 빈칸을 고치고 다시 버튼을 누르세요.")
    
    else:
        st.info("위 빈칸에 기준을 먼저 입력해주세요.")
