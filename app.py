import streamlit as st
import google.generativeai as genai

# --------------------------------------------------------------------------
# 1. 페이지 설정
# --------------------------------------------------------------------------
st.set_page_config(page_title="AHP 논리 정밀 진단기", page_icon="⚖️", layout="wide")

# --------------------------------------------------------------------------
# 2. 사이드바 (API 키 설정)
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
    st.info("💡 **진단 방식**\n- **요약**: 핵심 문제 3줄\n- **제안**: 개선 방향 1줄\n- **상세**: 클릭하여 확인")

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"키 설정 오류: {e}")

# --------------------------------------------------------------------------
# 3. AI 분석 함수 (데이터 파싱 로직 강화)
# --------------------------------------------------------------------------
def analyze_ahp_logic(goal, parent, children):
    if not children:
        return {
            "status": "NONE",
            "summary": "하위 항목이 입력되지 않았습니다.",
            "suggestion": "항목을 추가해주세요.",
            "detail": "분석할 데이터가 없습니다."
        }
    
    # AI에게 구분자(|)를 사용하여 명확하게 나누어 달라고 요청
    prompt = f"""
    [역할] AHP 논리 진단 컨설턴트
    [대상] 목표: {goal} / 상위: {parent} / 하위: {children}
    [기준] 독립성, MECE, 개수 적정성

    [출력 형식] - 아래 구분자(|)를 지켜서 출력할 것
    등급|요약|제안|상세
    
    1. 등급: [양호/주의/위험] 중 하나만 작성
    2. 요약: 핵심 진단 내용을 불렛포인트(-) 3개 이내로 간결하게 작성
    3. 제안: 가장 시급한 개선책 1문장 작성
    4. 상세: 논리적 근거와 구체적인 이유를 자세히 서술
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        
        # 결과 파싱 (구분자로 나누기)
        parts = text.split('|')
        
        # 형식이 깨졌을 경우를 대비한 예외처리
        if len(parts) < 4:
            return {
                "status": "주의",
                "summary": "AI 응답 형식이 불명확합니다.",
                "suggestion": "다시 시도해주세요.",
                "detail": text
            }
            
        return {
            "status": parts[0].replace("등급:", "").strip(),
            "summary": parts[1].replace("요약:", "").strip(),
            "suggestion": parts[2].replace("제안:", "").strip(),
            "detail": parts[3].replace("상세:", "").strip()
        }

    except Exception as e:
        return {"status": "에러", "summary": f"통신 오류: {e}", "suggestion": "", "detail": ""}

# --------------------------------------------------------------------------
# 4. 결과 UI 렌더링 함수 (접기/펼치기 적용)
# --------------------------------------------------------------------------
def render_result_ui(title, result_data, count_msg=""):
    status = result_data['status']
    
    # 상태별 색상 및 아이콘 설정
    if "위험" in status:
        icon = "🚨"
        header_color = "red"
        bg_color = "#FFF5F5"
    elif "주의" in status:
        icon = "⚠️"
        header_color = "orange"
        bg_color = "#FFFDF5"
    else:
        icon = "✅"
        header_color = "green"
        bg_color = "#F0FDF4"

    # 컨테이너 박스 생성
    with st.container(border=True):
        # 1. 헤더 (아이콘 + 제목 + 등급)
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"### {icon} :**{header_color}[{title}]**")
        with c2:
            st.markdown(f"**진단결과: :{header_color}[{status}]**")
        
        # 2. 개수 경고 메시지 (있을 경우만)
        if count_msg:
            st.error(count_msg)
            
        # 3. 핵심 요약 (3줄)
        st.markdown("**📋 핵심 진단**")
        st.markdown(result_data['summary'])
        
        # 4. 제안 (강조 박스)
        st.info(f"💡 **제안:** {result_data['suggestion']}")
        
        # 5. 상세 보기 (클릭해야 열림) - 여기가 요청하신 기능!
        with st.expander("🔍 상세 분석 사유 보기 (클릭)"):
            st.write(result_data['detail'])

# --------------------------------------------------------------------------
# 5. 메인 로직
# --------------------------------------------------------------------------
if 'main_count' not in st.session_state: st.session_state.main_count = 1 
if 'sub_counts' not in st.session_state: st.session_state.sub_counts = {}

st.title("⚖️ AHP 논리 진단 리포트 (Smart View)")
st.caption("복잡한 내용은 숨기고, 핵심만 보여줍니다. 자세한 내용은 클릭해서 확인하세요.")
st.divider()

if not api_key:
    st.warning("👈 사이드바에 API Key를 입력해주세요.")
    st.stop()

# 입력 1: 목표
col_goal, _ = st.columns([2, 1])
with col_goal:
    goal = st.text_input("🎯 최종 목표", placeholder="예: 차세대 전차 도입")

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
            with st.expander(f"📂 '{criterion}' 구성하기", expanded=True):
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
            with st.spinner("AI가 리포트를 생성하고 있습니다..."):
                
                # 1차 기준 진단
                st.subheader("📊 진단 리포트")
                res_main = analyze_ahp_logic(goal, goal, main_criteria)
                render_result_ui(f"1차 기준: {goal}", res_main)
                
                # 세부 항목 진단
                for parent, children in structure_data.items():
                    # 개수 경고 체크
                    msg = ""
                    if len(children) >= 8:
                        msg = f"⚠️ 항목이 {len(children)}개입니다. 7개 이하로 줄이는 것을 권장합니다."
                    elif len(children) == 1:
                        msg = "⚠️ 항목이 1개뿐입니다. 비교가 불가능합니다."
                    
                    # AI 분석
                    res = analyze_ahp_logic(goal, parent, children)
                    render_result_ui(f"세부항목: {parent}", res, msg)
