import streamlit as st
import google.generativeai as genai

# --------------------------------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------------------------------
st.set_page_config(page_title="AHP 논리 정밀 진단기", page_icon="⚖️", layout="wide")

# --------------------------------------------------------------------------
# 2. 사이드바
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("🔐 인증 설정")
    api_key = st.text_input(
        "Google API Key", 
        type="password",
        placeholder="AIzaSy... 키를 입력하세요",
        help="Google AI Studio에서 발급받은 키를 입력하세요."
    )
    st.divider()
    st.info("💡 **리포트 구조**\n1. 핵심 요약 (3줄)\n2. 조치 제안 (1줄)\n3. **추천 항목 (AI 모범답안)**\n4. 상세 분석")

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"키 설정 오류: {e}")

# --------------------------------------------------------------------------
# 3. AI 분석 함수 (예시 추천 기능 추가)
# --------------------------------------------------------------------------
def analyze_ahp_logic(goal, parent, children):
    if not children:
        return {
            "grade": "정보없음",
            "summary": "하위 항목이 없습니다.",
            "suggestion": "항목을 추가해주세요.",
            "example": "추천 항목 없음",
            "detail": "분석할 데이터가 없습니다."
        }
    
    # [핵심] AI에게 '구체적인 예시(EXAMPLE)'를 달라고 요청
    prompt = f"""
    [역할] AHP 논리 진단 컨설턴트
    [대상] 목표: {goal} / 상위: {parent} / 하위: {children}
    
    [지침]
    1. AHP 이론(독립성, MECE, 7±2 원칙)에 맞춰 냉철하게 평가하라.
    2. **반드시 수정된 '모범 항목 리스트'를 구체적인 단어로 추천하라.** (예: 항목이 부족하면 추가해주고, 중복되면 합쳐서 3~5개로 제안)
    
    [답변 양식] - 아래 태그를 반드시 지킬 것
    [GRADE]
    (양호, 주의, 위험 중 하나)
    
    [SUMMARY]
    (핵심 문제점 3줄 요약)
    
    [SUGGESTION]
    (가장 시급한 조치사항 1줄)
    
    [EXAMPLE]
    (가장 이상적인 하위 항목 구성 예시 3~5개 나열. 예: - 항목A, - 항목B, - 항목C)
    
    [DETAIL]
    (상세 논리 분석)
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        
        # 태그 파싱
        grade = "정보없음"
        summary = "정보 없음"
        suggestion = "정보 없음"
        example = "추천 없음"
        detail = text
        
        if "[GRADE]" in text:
            parts = text.split("[GRADE]")
            if len(parts) > 1:
                temp = parts[1].split("[SUMMARY]")
                grade = temp[0].strip()
                
                if len(temp) > 1:
                    temp2 = temp[1].split("[SUGGESTION]")
                    summary = temp2[0].strip()
                    
                    if len(temp2) > 1:
                        temp3 = temp2[1].split("[EXAMPLE]")
                        suggestion = temp3[0].strip()
                        
                        if len(temp3) > 1:
                            temp4 = temp3[1].split("[DETAIL]")
                            example = temp4[0].strip()
                            if len(temp4) > 1:
                                detail = temp4[1].strip()

        return {
            "grade": grade,
            "summary": summary,
            "suggestion": suggestion,
            "example": example,
            "detail": detail
        }

    except Exception as e:
        return {"grade": "에러", "summary": "통신 오류", "suggestion": "", "example": "", "detail": str(e)}

# --------------------------------------------------------------------------
# 4. 결과 UI 렌더링 (모범답안 카드 추가)
# --------------------------------------------------------------------------
def render_result_ui(title, data, count_msg=""):
    grade = data['grade']
    
    # 스타일 설정
    if "위험" in grade:
        icon = "🚨"
        color = "red"
        bg_color = "#fee"
    elif "주의" in grade:
        icon = "⚠️"
        color = "orange"
        bg_color = "#fffae5"
    else:
        icon = "✅"
        color = "green"
        bg_color = "#eff"

    with st.container(border=True):
        # 헤더
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"#### {icon} {title}")
        with c2:
            st.markdown(f"**등급: :{color}[{grade}]**")
            
        if count_msg:
            st.caption(f":red[{count_msg}]")
        
        st.divider()
        
        # 요약
        st.markdown("**📋 핵심 요약**")
        st.markdown(data['summary'])
        
        # 제안
        st.markdown(f"**💡 조치 제안:** {data['suggestion']}")
        
        # [NEW] AI 추천 예시 (여기가 추가된 부분!)
        if "없음" not in data['example']:
            st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; margin-top: 10px; margin-bottom: 10px;">
                <strong style="color: {color};">✨ AI 추천 구성 (모범 답안)</strong>
                <div style="margin-top: 5px; font-size: 0.95em;">
                    {data['example'].replace('\n', '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # 상세 보기
        with st.expander("🔍 상세 분석 사유 보기"):
            st.write(data['detail'])

# --------------------------------------------------------------------------
# 5. 메인 로직
# --------------------------------------------------------------------------
if 'main_count' not in st.session_state: st.session_state.main_count = 1 
if 'sub_counts' not in st.session_state: st.session_state.sub_counts = {}

st.title("⚖️ AHP 논리 진단 리포트 (Pro)")
st.caption("AI가 오류를 진단하고, **가장 적절한 대체 항목 예시**까지 추천해줍니다.")
st.divider()

if not api_key:
    st.warning("👈 사이드바에 API Key를 입력해주세요.")
    st.stop()

# 입력 1: 목표
col_goal, _ = st.columns([2, 1])
with col_goal:
    goal = st.text_input("🎯 최종 목표", placeholder="예: 차세대 전투기 도입")

if goal:
    # 입력 2: 기준
    st.subheader("1. 기준 설정")
    main_criteria = []
    for i in range(st.session_state.main_count):
        val = st.text_input(f"기준 {i+1}", key=f"main_{i}")
        if val: main_criteria.append(val)
    
    if st.button("➕ 기준 추가"):
        st.session_state.main_count += 1
        st.rerun()

    # 입력 3: 세부 항목
    structure_data = {}
    if main_criteria:
        st.divider()
        st.subheader("2. 세부 항목 구성")
        for criterion in main_criteria:
            with st.expander(f"📂 '{criterion}' 하위 요소", expanded=True):
                if criterion not in st.session_state.sub_counts:
                    st.session_state.sub_counts[criterion] = 1
                
                sub_items = []
                for j in range(st.session_state.sub_counts[criterion]):
                    s_val = st.text_input(f"ㄴ {criterion}-{j+1}", key=f"sub_{criterion}_{j}")
                    if s_val: sub_items.append(s_val)
                
                if st.button("➕ 추가", key=f"btn_{criterion}"):
                    st.session_state.sub_counts[criterion] += 1
                    st.rerun()
                structure_data[criterion] = sub_items

        # 진단 시작
        st.divider()
        if st.button("🚀 AI 진단 및 추천 받기", type="primary", use_container_width=True):
            with st.spinner("AI가 최적의 항목을 구성하고 있습니다..."):
                
                st.subheader("📊 진단 리포트")
                # 1차 기준
                res_main = analyze_ahp_logic(goal, goal, main_criteria)
                render_result_ui(f"1차 기준: {goal}", res_main)
                
                # 세부 항목
                for parent, children in structure_data.items():
                    msg = ""
                    if len(children) >= 8:
                        msg = f"⚠️ 항목이 {len(children)}개입니다. (7±2 원칙 초과)"
                    elif len(children) == 1:
                        msg = "⚠️ 항목이 1개뿐입니다. (비교 불가)"
                    
                    res = analyze_ahp_logic(goal, parent, children)
                    render_result_ui(f"세부항목: {parent}", res, msg)
