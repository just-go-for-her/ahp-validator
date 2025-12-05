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
    st.info("💡 **리포트 구조**\n1. 핵심 요약 (3줄)\n2. 조치 제안 (1줄)\n3. 상세 분석 (클릭 시 확장)")

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"키 설정 오류: {e}")

# --------------------------------------------------------------------------
# 3. AI 분석 함수 (파싱 오류 방지를 위한 구분자 강화)
# --------------------------------------------------------------------------
def analyze_ahp_logic(goal, parent, children):
    if not children:
        return {
            "grade": "정보없음",
            "summary": "하위 항목이 없습니다.",
            "suggestion": "항목을 추가해주세요.",
            "detail": "분석할 데이터가 없습니다."
        }
    
    # AI에게 '구분 태그'를 써서 답해달라고 강력하게 요청
    prompt = f"""
    [역할] AHP 논리 진단 컨설턴트
    [대상] 목표: {goal} / 상위: {parent} / 하위: {children}
    
    [지침] 
    1. AHP 이론(독립성, MECE, 계층구조)에 입각하여 냉철하게 평가하라.
    2. 답변은 반드시 아래 4가지 태그로 구분하여 작성하라. 태그 외에 다른 말은 쓰지 마라.
    
    [답변 양식]
    [GRADE]
    (양호, 주의, 위험 중 단어 하나만 작성)
    
    [SUMMARY]
    (핵심 문제점이나 현황을 - 기호를 써서 3줄 이내로 요약)
    
    [SUGGESTION]
    (가장 시급한 조치사항 1줄 작성)
    
    [DETAIL]
    (구체적인 근거와 논리적 분석 내용 서술)
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        
        # 태그를 기준으로 텍스트 쪼개기 (파싱)
        grade = "정보없음"
        summary = "요약 정보를 불러오지 못했습니다."
        suggestion = "제안 사항이 없습니다."
        detail = text # 기본값은 전체 텍스트
        
        # 파싱 로직
        if "[GRADE]" in text:
            parts = text.split("[GRADE]")
            if len(parts) > 1:
                # [GRADE] 뒷부분을 다시 [SUMMARY]로 쪼갬
                temp = parts[1].split("[SUMMARY]")
                grade = temp[0].strip()
                
                if len(temp) > 1:
                    temp2 = temp[1].split("[SUGGESTION]")
                    summary = temp2[0].strip()
                    
                    if len(temp2) > 1:
                        temp3 = temp2[1].split("[DETAIL]")
                        suggestion = temp3[0].strip()
                        if len(temp3) > 1:
                            detail = temp3[1].strip()

        return {
            "grade": grade,
            "summary": summary,
            "suggestion": suggestion,
            "detail": detail
        }

    except Exception as e:
        return {"grade": "에러", "summary": "통신 오류 발생", "suggestion": "API Key를 확인하세요", "detail": str(e)}

# --------------------------------------------------------------------------
# 4. 결과 UI 렌더링 (순정 Streamlit 기능 사용 - 코드노출 해결)
# --------------------------------------------------------------------------
def render_result_ui(title, data, count_msg=""):
    grade = data['grade']
    
    # 등급별 스타일 설정
    if "위험" in grade:
        icon = "🚨"
        color = "red"
        box_type = "error" # 붉은색 박스
    elif "주의" in grade:
        icon = "⚠️"
        color = "orange"
        box_type = "warning" # 노란색 박스
    else:
        icon = "✅"
        color = "green"
        box_type = "success" # 초록색 박스

    # 1. 메인 컨테이너 (박스)
    with st.container(border=True):
        
        # 2. 헤더 (제목 + 등급)
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"#### {icon} {title}")
        with c2:
            st.markdown(f"**등급: :{color}[{grade}]**")
            
        # 3. 개수 경고 (있을 때만 표시)
        if count_msg:
            st.caption(f":red[{count_msg}]")
        
        st.divider()
        
        # 4. 핵심 요약 (3줄)
        st.markdown("**📋 핵심 요약**")
        st.markdown(data['summary'])
        
        # 5. 제안 (강조)
        if box_type == "error":
            st.error(f"💡 **제안:** {data['suggestion']}")
        elif box_type == "warning":
            st.warning(f"💡 **제안:** {data['suggestion']}")
        else:
            st.success(f"💡 **제안:** {data['suggestion']}")
        
        # 6. 상세 보기 (클릭해야 열림 - 여기가 핵심!)
        with st.expander("🔍 상세 분석 사유 보기 (클릭)"):
            st.write(data['detail'])

# --------------------------------------------------------------------------
# 5. 메인 로직
# --------------------------------------------------------------------------
if 'main_count' not in st.session_state: st.session_state.main_count = 1 
if 'sub_counts' not in st.session_state: st.session_state.sub_counts = {}

st.title("⚖️ AHP 논리 진단 리포트")
st.caption("AI가 3가지 관점(독립성, MECE, 계층구조)에서 정밀 진단합니다.")
st.divider()

if not api_key:
    st.warning("👈 사이드바에 API Key를 입력해주세요.")
    st.stop()

# [입력 1] 목표
col_goal, _ = st.columns([2, 1])
with col_goal:
    goal = st.text_input("🎯 최종 목표", placeholder="예: 차세대 전투기 도입")

if goal:
    # [입력 2] 기준
    st.subheader("1. 기준 설정")
    main_criteria = []
    for i in range(st.session_state.main_count):
        val = st.text_input(f"기준 {i+1}", key=f"main_{i}")
        if val: main_criteria.append(val)
    
    if st.button("➕ 기준 추가"):
        st.session_state.main_count += 1
        st.rerun()

    # [입력 3] 세부 항목
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

        # [진단 시작]
        st.divider()
        if st.button("🚀 AI 정밀 진단 시작", type="primary", use_container_width=True):
            with st.spinner("AI가 분석 리포트를 작성하고 있습니다..."):
                
                # 1차 기준 분석
                st.subheader("📊 진단 리포트")
                res_main = analyze_ahp_logic(goal, goal, main_criteria)
                render_result_ui(f"1차 기준: {goal}", res_main)
                
                # 세부 항목 분석
                for parent, children in structure_data.items():
                    # 개수 경고 메시지
                    msg = ""
                    if len(children) >= 8:
                        msg = f"⚠️ 항목이 {len(children)}개입니다. (7±2 원칙 초과)"
                    elif len(children) == 1:
                        msg = "⚠️ 항목이 1개뿐입니다. (비교 불가)"
                    
                    res = analyze_ahp_logic(goal, parent, children)
                    render_result_ui(f"세부항목: {parent}", res, msg)
