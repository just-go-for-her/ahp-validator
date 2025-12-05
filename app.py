import streamlit as st

# 페이지 설정
st.set_page_config(page_title="직관적 의사결정 트리", layout="wide")

st.title("🌳 직관적 의사결정 도우미 (Branch Mode)")
st.markdown("복잡한 코드는 잊으세요. 빈칸을 채우면 생각이 정리됩니다.")

# 1. 목표 설정
st.subheader("1. 무엇을 결정하고 싶으신가요?")
goal = st.text_input("목표를 입력하세요 (예: 국방 AI 시스템 도입)", placeholder="여기에 목표 입력")

if goal:
    st.divider()
    st.subheader(f"2. '{goal}'을(를) 위한 핵심 기준 3가지")
    st.info("가장 중요하게 생각하는 기준을 최대 3개만 적어주세요.")

    # 1차 기준 입력 (3개의 컬럼으로 나누어 빈칸 제시)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        c1 = st.text_input("기준 1", placeholder="예: 작전효율성")
    with col2:
        c2 = st.text_input("기준 2", placeholder="예: 비용")
    with col3:
        c3 = st.text_input("기준 3", placeholder="예: 기술신뢰도")

    # 입력된 기준들을 리스트로 정리
    criteria_list = [c for c in [c1, c2, c3] if c] # 빈칸이 아닌 것만 가져오기

    if criteria_list:
        st.divider()
        st.subheader("3. 세부 항목 가지치기 (+ 계층 추가)")
        st.markdown("각 기준을 클릭하면 세부 항목(하위 가지)을 입력할 수 있는 빈칸이 나옵니다.")

        # 입력된 각 기준에 대해 하위 항목 입력창 생성 (Expander 활용)
        results = {} # 전체 구조를 저장할 딕셔너리
        
        for criterion in criteria_list:
            # st.expander를 사용하여 '브랜치' 느낌 구현 (누르면 열림)
            with st.expander(f"➕ '{criterion}'의 세부 항목 추가하기", expanded=True):
                st.markdown(f"**{criterion}**을 구성하는 하위 요소 3가지는?")
                
                # 하위 항목도 3개로 제한 (컬럼 분리)
                sub_c1, sub_c2, sub_c3 = st.columns(3)
                
                # key값을 유니크하게 주어야 에러가 안 남
                s1 = sub_c1.text_input(f"{criterion}-세부1", placeholder="항목 1", label_visibility="collapsed")
                s2 = sub_c2.text_input(f"{criterion}-세부2", placeholder="항목 2", label_visibility="collapsed")
                s3 = sub_c3.text_input(f"{criterion}-세부3", placeholder="항목 3", label_visibility="collapsed")
                
                # 입력된 하위 항목 저장
                sub_items = [s for s in [s1, s2, s3] if s]
                results[criterion] = sub_items

        # 4. 최종 구조 확인
        st.divider()
        st.subheader("4. 완성된 구조 확인")
        
        # 시각적으로 보여주기 (JSON 대신 트리 형태로 텍스트 출력)
        st.markdown(f"### 🎯 목표: {goal}")
        for main_c, subs in results.items():
            st.markdown(f"- **{main_c}**")
            if subs:
                for sub in subs:
                    st.markdown(f"  - └ {sub}")
            else:
                st.markdown("  - (세부 항목 없음)")
        
        st.success("구조가 완성되었습니다! (다음 단계: 분석 시작하기)")

    else:
        st.warning("위의 빈칸에 기준을 하나 이상 입력해주세요.")

else:
    st.write("먼저 목표를 입력해주세요.")
