import streamlit as st
import google.generativeai as genai

# --------------------------------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------------------------------
st.set_page_config(page_title="AHP 논리 정밀 진단기", page_icon="⚖️", layout="wide")

# --------------------------------------------------------------------------
# 2. API 키 인증 처리 (하이브리드 방식)
# --------------------------------------------------------------------------
# 시스템 설계자(당신)를 위한 자동 로그인 로직
api_key = None

# 1순위: Streamlit Secrets(비밀금고)에서 키를 찾음
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]

# 2순위: Secrets에 없으면 사이드바에서 입력받음 (백업용)
else:
    with st.sidebar:
        st.header("🔐 인증 설정")
        api_key = st.text_input(
            "Google API Key", 
            type="password",
            placeholder="비밀 금고에 키가 없습니다.",
            help="Streamlit Secrets 설정을 완료하면 이 입력창은 사라집니다."
        )

# --------------------------------------------------------------------------
# 3. 모델 설정
# --------------------------------------------------------------------------
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"키 설정 오류: {e}")
        st.stop()
else:
    # 키가 없으면 화면을 가리고 안내 메시지 출력
    st.warning("⚠️ 시스템을 가동하려면 API 키가 필요합니다.")
    st.info("💡 **설계자 팁:** Streamlit Cloud > Settings > Secrets 에 키를 등록하면 자동 로그인됩니다.")
    st.stop()

# --------------------------------------------------------------------------
# 4. AI 분석 함수 (등급/요약/제안/예시/상세)
# --------------------------------------------------------------------------
def analyze_ahp_logic(goal, parent, children):
    if not children:
        return {
            "grade": "정보없음",
            "summary": "하위 항목이 없습니다.",
            "suggestion": "항목을 추가해주세요.",
            "example": "추천 없음",
            "detail": "분석할 데이터가 없습니다."
        }
    
    prompt = f"""
    [역할] AHP 논리 진단 컨설턴트
    [대상] 목표: {goal} / 상위: {parent} / 하위: {children}
    
    [지침]
    1. AHP 이론(독립성, MECE, 7±2 원칙)에 맞춰 냉철하게 평가하라.
    2. **반드시 수정된 '모범 항목 리스트'를 구체적인 단어로 추천하라.**
    
    [답변 양식]
    [GRADE]
    (양호, 주의, 위험 중 하나)
    [SUMMARY]
    (핵심 문제점 3줄 요약)
    [SUGGESTION]
    (가장 시급한 조치사항 1줄)
    [EXAMPLE]
    (가장 이상적인 하위 항목 구성 예시 3~5개 나열)
    [DETAIL]
    (상세 논리 분석)
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        
        # 기본값 설정
        data = {
            "grade": "정보없음", "summary": "정보 없음", 
            "suggestion": "정보 없음", "example": "추천 없음", "detail": text
        }
        
        if "[GRADE]" in text:
            parts = text.split("[GRADE]")
            if len(parts) > 1:
                temp = parts[1].split("[SUMMARY]")
                data["grade"] = temp[0].strip()
                if len(temp) > 1:
                    temp2 = temp[1].split("[SUGGESTION]")
                    data["summary"] = temp2[0].strip()
                    if len(temp2) > 1:
                        temp3 = temp2[1].split("[EXAMPLE]")
                        data["suggestion"] = temp3[0].strip()
                        if len(temp3) > 1:
                            temp4 = temp3[1].split("[DETAIL]")
                            data["example"] = temp4[0].strip()
                            if len(temp4) > 1:
                                data["detail"] = temp4[1].strip()
        return data

    except Exception as e:
        return {"grade": "에러", "summary": "통신 오류", "suggestion": "", "example": "", "detail": str(e)}

# --------------------------------------------------------------------------
# 5. 결과 UI 렌더링
# --------------------------------------------------------------------------
def render_result_ui(title, data, count_msg=""):
    grade = data['grade']
    if "위험" in grade:
        icon, color, bg = "🚨", "red", "#fee"
    elif "주의" in grade:
        icon, color, bg = "⚠️", "orange", "#fffae5"
    else:
        icon, color, bg = "✅", "green", "#eff"

    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1: st.markdown(f"#### {icon} {title}")
        with c2: st.markdown(f"**등급: :{color}[{grade}]**")
        
        if count_msg: st.caption(f":red[{count_msg}]")
        st.divider()
        st.markdown("**📋 핵심 요약**")
        st.markdown(data['summary'])
        st.markdown(f"**💡 조치 제안:** {data['suggestion']}")
        
        if "없음" not in data['example']:
            st.markdown(f"""
            <div style="background-color: {bg}; padding: 15px; border-radius: 10px; margin: 10px 0;">
                <strong style="color: {color};">✨ AI 추천 구성 (모범 답안)</strong>
                <div style="margin-top: 5px; font-size: 0.95em;">
                    {data['example'].replace('\n', '<br>')}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with st.expander("🔍 상세 분석 사유 보기"):
            st.write(data['detail'])

# --------------------------------------------------------------------------
# 6. 메인 로직
# --------------------------------------------------------------------------
if 'main_count' not in st.session_state: st.session_state.main_count = 1 
if 'sub_counts' not in st.session_state: st.session_state.sub_counts = {}

# 사이드바 설명 (키 입력창 제거됨 - Secrets 사용 시)
with st.sidebar:
    st.info("💡 **리포트 구조**\n1. 요약 (3줄)\n2. 제안 (1줄)\n3. **추천 (모범답안)**\n4. 상세")

st.title("⚖️ AHP 논리 진단 리포트 (Pro)")
st.caption("AI가 오류를 진단하고, **가장 적절한 대체 항목 예시**까지 추천해줍니다.")
st.divider()

col_goal, _ = st.columns([2, 1])
with col_goal:
    goal = st.text_input("🎯 최종 목표", placeholder="예: 차세대 전투기 도입")

if goal:
    st.subheader("1. 기준 설정")
    main_criteria = []
    for i in range(st.session_state.main_count):
        val = st.text_input(f"기준 {i+1}", key=f"main_{i}")
        if val: main_criteria.append(val)
    if st.button("➕ 기준 추가"):
        st.session_state.main_count += 1
        st.rerun()

    structure_data = {}
    if main_criteria:
        st.divider()
        st.subheader("2. 세부 항목 구성")
        for criterion in main_criteria:
            with st.expander(f"📂 '{criterion}' 하위 요소", expanded=True):
                if criterion not in st.session_state.sub_counts: st.session_state.sub_counts[criterion] = 1
                sub_items = []
                for j in range(st.session_state.sub_counts[criterion]):
                    s_val = st.text_input(f"ㄴ {criterion}-{j+1}", key=f"sub_{criterion}_{j}")
                    if s_val: sub_items.append(s_val)
                if st.button("➕ 추가", key=f"btn_{criterion}"):
                    st.session_state.sub_counts[criterion] += 1
                    st.rerun()
                structure_data[criterion] = sub_items

        st.divider()
        if st.button("🚀 AI 진단 및 추천 받기", type="primary", use_container_width=True):
            with st.spinner("AI가 최적의 항목을 구성하고 있습니다..."):
                res_main = analyze_ahp_logic(goal, goal, main_criteria)
                render_result_ui(f"1차 기준: {goal}", res_main)
                for p, c in structure_data.items():
                    msg = ""
                    if len(c) >= 8: msg = f"⚠️ 항목 {len(c)}개 (7±2 초과)"
                    elif len(c) == 1: msg = "⚠️ 항목 1개 (비교 불가)"
                    res = analyze_ahp_logic(goal, p, c)
                    render_result_ui(f"세부항목: {p}", res, msg)
