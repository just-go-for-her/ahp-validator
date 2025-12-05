import streamlit as st
import google.generativeai as genai

# --------------------------------------------------------------------------
# 1. 페이지 설정 및 디자인(CSS) 주입
# --------------------------------------------------------------------------
st.set_page_config(page_title="AHP 논리 정밀 진단기", page_icon="⚖️", layout="wide")

# 깔끔한 리포트 출력을 위한 커스텀 CSS
st.markdown("""
<style>
    /* 전체 폰트 및 배경 설정 */
    .report-card {
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .card-danger { background-color: #FFF5F5; border-left: 6px solid #FF4B4B; }
    .card-warning { background-color: #FFFDF5; border-left: 6px solid #FFA421; }
    .card-success { background-color: #F0FDF4; border-left: 6px solid #21C354; }
    
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9em;
        color: white;
        margin-bottom: 10px;
    }
    .badge-danger { background-color: #FF4B4B; }
    .badge-warning { background-color: #FFA421; }
    .badge-success { background-color: #21C354; }

    .card-title { font-size: 1.2em; font-weight: bold; color: #333; display: inline-block; margin-left: 10px;}
    .section-title { font-weight: bold; color: #555; margin-top: 10px; margin-bottom: 5px; }
    .content-text { color: #444; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

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
    st.markdown("---")
    st.info("""
    **💡 진단 포인트**
    1. **독립성**: 항목 간 인과관계 여부
    2. **MECE**: 중복되거나 빠진 내용 여부
    3. **균형**: 항목 개수의 적절성 (7±2)
    """)

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        st.error(f"키 설정 오류: {e}")

# --------------------------------------------------------------------------
# 3. AI 분석 함수 (구조적 출력 요청)
# --------------------------------------------------------------------------
def analyze_ahp_logic(goal, parent, children):
    if not children:
        return {"status": "NONE", "text": "하위 항목이 없습니다."}
    
    # 디자인 적용을 위해 AI에게 명확한 포맷 요청
    prompt = f"""
    당신은 AHP 방법론 검증 전문가입니다.
    
    [분석 대상]
    - 최종목표: {goal}
    - 기준명: {parent}
    - 하위요소: {children}

    [진단 기준]
    1. 독립성 위반 (인과관계가 섞였는가?)
    2. MECE 위반 (중복되거나 누락되었는가?)
    3. 논리적 타당성

    [출력 형식]
    반드시 아래 형식에 맞춰 답변하세요.
    
    등급: [양호/주의/위험]
    한줄요약: (전체적인 평가를 15자 이내로 요약)
    상세분석: (위반 사항이나 잘된 점을 구체적으로 설명, 줄바꿈 가능)
    조치제안: (수정이 필요하다면 구체적인 대안 제시)
    """
    
    try:
        response = model.generate_content(prompt)
        return {"text": response.text}
    except Exception as e:
        return {"text": f"통신 오류: {e}"}

# --------------------------------------------------------------------------
# 4. 결과 카드 렌더링 함수 (HTML 생성기)
# --------------------------------------------------------------------------
def render_result_card(title, result_text, count_msg=""):
    # AI 응답 파싱 (등급 색출)
    if "위험" in result_text:
        card_class = "card-danger"
        badge_class = "badge-danger"
        status_text = "위험 (Critical)"
        icon = "🚨"
    elif "주의" in result_text:
        card_class = "card-warning"
        badge_class = "badge-warning"
        status_text = "주의 (Warning)"
        icon = "⚠️"
    else:
        card_class = "card-success"
        badge_class = "badge-success"
        status_text = "양호 (Good)"
        icon = "✅"

    # 텍스트 포맷팅 (줄바꿈 처리)
    formatted_text = result_text.replace("\n", "<br>")
    
    # 개수 경고 메시지가 있으면 빨간색으로 강조
    count_html = f"<div style='color: #d9534f; font-weight: bold; margin-bottom: 10px;'>{count_msg}</div>" if count_msg else ""

    # HTML 조립
    html_code = f"""
    <div class="report-card {card_class}">
        <div>
            <span class="status-badge {badge_class}">{status_text}</span>
            <span class="card-title">{title}</span>
        </div>
        <hr style="margin: 10px 0; border-top: 1px solid #ddd;">
        {count_html}
        <div class="content-text">
            {formatted_text}
        </div>
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)

# --------------------------------------------------------------------------
# 5. 메인 로직 및 UI
# --------------------------------------------------------------------------
# 세션 초기화
if 'main_count' not in st.session_state: st.session_state.main_count = 1 
if 'sub_counts' not in st.session_state: st.session_state.sub_counts = {}

st.title("⚖️ AHP 구조 논리 진단 리포트")
st.markdown("독립성, MECE, 가중치 희석 등을 종합적으로 평가하여 **컨설팅 리포트** 형태로 제공합니다.")
st.divider()

if not api_key:
    st.warning("👈 먼저 왼쪽 사이드바에 Google API Key를 입력해주세요.")
    st.stop()

# [입력 1] 목표 및 1차 기준
col_goal, _ = st.columns([2, 1])
with col_goal:
    goal = st.text_input("🎯 최종 목표", placeholder="예: 차세대 무기체계 선정")

if goal:
    st.subheader("1. 평가 기준 설정")
    main_criteria = []
    
    # 동적 입력창
    for i in range(st.session_state.main_count):
        col_in, _ = st.columns([4, 1])
        with col_in:
            val = st.text_input(f"기준 {i+1}", key=f"main_{i}", placeholder="항목 입력")
            if val: main_criteria.append(val)
    
    if st.button("➕ 기준 추가"):
        st.session_state.main_count += 1
        st.rerun()

    # [입력 2] 하위 항목 설정
    structure_data = {}
    if main_criteria:
        st.divider()
        st.subheader("2. 세부 구조 설계")
        
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

        # [출력] 진단 리포트
        st.divider()
        st.subheader("📊 진단 결과 리포트")
        
        if st.button("🚀 정밀 진단 시작", type="primary", use_container_width=True):
            with st.spinner("AI 컨설턴트가 보고서를 작성 중입니다..."):
                
                # 상단 요약 배너
                total_sub = sum(len(v) for v in structure_data.values())
                c1, c2, c3 = st.columns(3)
                c1.metric("1차 기준", f"{len(main_criteria)}개")
                c2.metric("세부 항목", f"{total_sub}개")
                c3.metric("구조 복잡도", "높음" if total_sub > 15 else "적정")
                
                st.markdown("<br>", unsafe_allow_html=True)

                # 1. 메인 기준 진단
                res_main = analyze_ahp_logic(goal, goal, main_criteria)
                render_result_card(f"1차 기준: {goal}", res_main['text'])
                
                # 2. 세부 항목 진단 Loop
                for parent, children in structure_data.items():
                    # 파이썬 레벨의 개수 경고 메시지 생성
                    msg = ""
                    if len(children) >= 8:
                        msg = f"⚠️ [Guide Check] 하위 항목이 {len(children)}개입니다. 7개 이하로 줄이거나 그룹화(Sub-cluster)가 필요합니다."
                    elif len(children) == 1:
                        msg = "⚠️ [Guide Check] 하위 항목이 1개입니다. 상위 기준과 동일하여 분석 의미가 없습니다."
                    
                    # AI 분석 실행
                    res = analyze_ahp_logic(goal, parent, children)
                    
                    # 카드 출력
                    render_result_card(f"세부항목: {parent}", res['text'], msg)
