import streamlit as st
import google.generativeai as genai
import re  # [NEW] 정규표현식 모듈 추가 (텍스트 추출 강화)

# --------------------------------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------------------------------
st.set_page_config(page_title="AHP 논리 정밀 진단기", page_icon="⚖️", layout="wide")

# --------------------------------------------------------------------------
# 2. 인증 설정
# --------------------------------------------------------------------------
api_key = None
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    with st.sidebar:
        st.header("🔐 인증 설정")
        api_key = st.text_input("Google API Key", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"키 설정 오류: {e}")
        st.stop()
else:
    st.warning("⚠️ API 키가 필요합니다.")
    st.stop()

# --------------------------------------------------------------------------
# 3. AI 분석 함수 (정규표현식으로 무조건 추출)
# --------------------------------------------------------------------------
def analyze_ahp_logic(goal, parent, children):
    if not children:
        return {
            "grade": "정보없음", "summary": "하위 항목 없음", 
            "suggestion": "항목 추가 필요", "example": "추천 없음", "detail": "데이터 없음"
        }
    
    # [강화된 프롬프트] 무조건 예시를 쓰라고 압박
    prompt = f"""
    [역할] AHP 논리 진단 컨설턴트
    [대상] 목표: {goal} / 상위: {parent} / 하위: {children}
    
    [지침]
    1. 현재 구조가 논리적으로 '위험'하더라도, 사용자가 참고할 수 있는 **[EXAMPLE] (모범 답안)**을 무조건 작성하라.
    2. 양호하다면 현재 항목을 그대로 예시로 들어라.
    
    [필수 출력 태그] - 이 태그를 빠뜨리지 마시오.
    [GRADE] (양호/주의/위험)
    [SUMMARY] (3줄 요약)
    [SUGGESTION] (1줄 제안)
    [EXAMPLE] (수정된 모범 항목 리스트 3~5개, 불렛포인트 사용)
    [DETAIL] (상세 분석)
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        
        # [NEW] 정규표현식(Regex)을 이용한 안전한 파싱
        # 태그가 중간에 섞여도 내용을 정확히 발라냅니다.
        def extract_content(tag, text):
            # [TAG]와 다음 [TAG] 사이의 내용을 찾음
            pattern = fr"\[{tag}\](.*?)(?=\[|$)" 
            match = re.search(pattern, text, re.DOTALL)
            return match.group(1).strip() if match else "내용 없음"

        data = {
            "grade": extract_content("GRADE", text),
            "summary": extract_content("SUMMARY", text),
            "suggestion": extract_content("SUGGESTION", text),
            "example": extract_content("EXAMPLE", text),
            "detail": extract_content("DETAIL", text)
        }
        
        # 만약 Regex가 실패했을 경우를 대비한 안전장치
        if data["grade"] == "내용 없음":
            data["grade"] = "주의"
            data["detail"] = text # 원문 전체 표시

        return data

    except Exception as e:
        return {"grade": "에러", "summary": "오류", "suggestion": "", "example": "", "detail": str(e)}

# --------------------------------------------------------------------------
# 4. UI 렌더링
# --------------------------------------------------------------------------
def render_result_ui(title, data, count_msg=""):
    grade = data['grade']
    
    # 등급별 색상 처리
    if "위험" in grade:
        icon, color, bg = "🚨", "red", "#fee"
    elif "주의" in grade:
        icon, color, bg = "⚠️", "orange", "#fffae5"
    elif "양호" in grade:
        icon, color, bg = "✅", "green", "#eff"
    else:
        icon, color, bg = "❓", "gray", "#eee"

    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1: st.markdown(f"#### {icon} {title}")
        with c2: st.markdown(f"**등급: :{color}[{grade}]**")
        
        if count_msg: st.caption(f":red[{count_msg}]")
        st.divider()
        
        st.markdown("**📋 핵심 요약**")
        st.markdown(data['summary'])
        
        # 제안 (등급에 따라 색상 다르게)
        if "양호" in grade:
            st.success(f"💡 **제안:** {data['suggestion']}")
        elif "위험" in grade:
            st.error(f"💡 **제안:** {data['suggestion']}")
        else:
            st.warning(f"💡 **제안:** {data['suggestion']}")
        
        # [중요] 추천 예시 박스 (내용이 '없음'이 아닐 때만 출력)
        if len(data['example']) > 5 and "없음" not in data['example']:
            st.markdown(f"""
            <div style="background-color: {bg}; padding: 15px; border-radius: 10px; margin: 10px 0; border: 1px solid {color};">
                <strong style="color: {color};">✨ AI 추천 모범 답안</strong>
                <div style="margin-top: 5px; font-size: 0.95em; white-space: pre-line;">
                    {data['example']}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with st.expander("🔍 상세 분석 사유 보기"):
            st.write(data['detail'])

# --------------------------------------------------------------------------
# 5. 메인 로직
# --------------------------------------------------------------------------
if 'main_count' not in st.session_state: st.session_state.main_count = 1 
if 'sub_counts' not in st.session_state: st.session_state.sub_counts = {}

with st.sidebar:
    st.info("💡 **리포트 구조**\n1. 요약 (3줄)\n2. 제안 (1줄)\n3. **추천 (모범답안)**\n4. 상세")

st.title("⚖️ AHP 논리 진단 리포트 (Pro)")
st.caption("AI가 오류를 진단하고, **반드시 모범 답안(Example)**을 제시합니다.")
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
            with st.spinner("AI가 분석 중입니다..."):
                res_main = analyze_ahp_logic(goal, goal, main_criteria)
                render_result_ui(f"1차 기준: {goal}", res_main)
                for p, c in structure_data.items():
                    msg = ""
                    if len(c) >= 8: msg = f"⚠️ 항목 {len(c)}개 (7±2 초과)"
                    elif len(c) == 1: msg = "⚠️ 항목 1개 (비교 불가)"
                    res = analyze_ahp_logic(goal, p, c)
                    render_result_ui(f"세부항목: {p}", res, msg)
