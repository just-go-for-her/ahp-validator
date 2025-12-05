import streamlit as st
import json
import google.generativeai as genai

# --- 1. 페이지 설정 ---
st.set_page_config(
    page_title="AHP 논리 진단기",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 AHP 연구 설계 자동 진단 솔루션")
st.markdown("""
이 도구는 **Gemini 2.5 AI**를 활용하여 AHP 계층 구조의 
**수학적 오류(Miller's Law)**와 **논리적 오류(독립성, MECE)**를 실시간으로 진단합니다.
""")

# --- 2. 사이드바: 설정 ---
with st.sidebar:
    st.header("⚙️ 설정 (Settings)")
    # 보안을 위해 API 키는 코드에 넣지 않고 화면에서 입력받습니다.
    api_key = st.text_input(
        "Google API Key 입력", 
        type="password",
        help="Google AI Studio에서 발급받은 키를 입력하세요. 저장은 되지 않습니다."
    )
    
    st.info("💡 팁: 상위 항목 개수와 하위 항목의 논리적 관계를 중점적으로 봅니다.")
    st.markdown("---")
    st.caption("Developed by AHP Researcher")

# --- 3. Gemini 분석 함수 ---
def ask_gemini(model, parent, children):
    prompt = f"""
    [역할] AHP 방법론 전문가 (냉철한 분석가)
    [분석 대상] 상위 기준: '{parent}' / 하위 요소들: {children}
    [요청]
    이 구조에서 다음 두 가지 오류를 분석하시오.
    1. 독립성 위반 (인과관계가 섞여있는가?)
    2. MECE 위반 (의미가 중복되거나, 치명적으로 누락되었는가?)
    
    답변 형식:
    - 오류 발견 시: "🚨 **[오류 유형]**" 및 이유 설명
    - 문제 없음: "✅ **통과**" 및 이유 설명
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"통신 에러: {e}"

# --- 4. 메인 화면 ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 구조 입력 (JSON)")
    
    default_input = {
        "name": "미래 국방 AI 시스템 도입",
        "sub_criteria": [
            {
                "name": "작전 효율성",
                "sub_criteria": [
                    {"name": "타격 정밀도"}, {"name": "피아 식별 능력"}
                ] 
            },
            {
                "name": "비용",
                "sub_criteria": [
                    {"name": "초기 도입비"}
                ]
            }
        ]
    }
    
    json_str = st.text_area(
        "계층 구조를 JSON 형태로 입력하세요:", 
        value=json.dumps(default_input, indent=4, ensure_ascii=False),
        height=500
    )

with col2:
    st.subheader("📊 진단 리포트")
    
    if st.button("🚀 진단 시작", type="primary"):
        if not api_key:
            st.warning("⚠️ 왼쪽 사이드바에 API Key를 먼저 입력해주세요!")
        else:
            try:
                # 데이터 파싱
                data = json.loads(json_str)
                
                # Gemini 연결
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash') # 최신 모델 사용
                
                st.success("✅ 엔진 가동! 계층 구조를 스캔합니다...")
                
                # BFS 탐색으로 모든 노드 순회
                queue = [data]
                
                while queue:
                    node = queue.pop(0)
                    node_name = node.get("name", "Unknown")
                    children = node.get("sub_criteria", [])
                    children_names = [c["name"] for c in children]
                    
                    if children:
                        with st.expander(f"📂 분석 중: **{node_name}**", expanded=True):
                            
                            # [A] 구조적 진단
                            if len(children) > 9:
                                st.error(f"🔴 [구조 위험] 하위 요소가 {len(children)}개입니다. (Miller's Law 위반)")
                            elif len(children) == 1:
                                st.warning("🟡 [구조 주의] 하위 요소가 1개뿐입니다.")
                            else:
                                st.caption(f"🔵 구조 양호 ({len(children)}개 요소)")
                            
                            # [B] AI 논리 진단
                            with st.spinner("AI가 논리를 분석하고 있습니다..."):
                                feedback = ask_gemini(model, node_name, children_names)
                                st.markdown("---")
                                st.write(feedback)
                        
                        # 자식 노드 큐에 추가
                        for child in children:
                            queue.append(child)
                            
                st.balloons() # 축하 효과 🎉
                st.success("모든 분석이 완료되었습니다.")
                
            except json.JSONDecodeError:
                st.error("🚨 JSON 형식이 틀렸습니다. 괄호나 콤마를 확인하세요.")
            except Exception as e:
                st.error(f"❌ 에러 발생: {e}")
