import streamlit as st
import google.generativeai as genai
import os

# 1. API 클라이언트 설정 (가장 단순한 방식)
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    # 처음 잘 됐던 1.5-flash 모델로 고정
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("API 키 설정이 잘못되었습니다.")
    st.stop()

# --- UI 레이아웃 ---
st.title("🎶 음악 추천 AI")
st.write("나이와 장르를 입력하면 음악을 추천해 드립니다.")

# 입력창
age = st.number_input("나이:", min_value=1, max_value=100, value=25)
genre = st.text_input("좋아하는 장르/가수:")

if st.button("음악 추천받기"):
    if not genre:
        st.warning("장르를 입력해주세요!")
    else:
        with st.spinner("추천 중..."):
            try:
                # 처음 코드처럼 복잡한 설정 없이 프롬프트 전달
                prompt = f"{age}세 사용자가 좋아할 만한 {genre} 음악 3곡을 추천하고 이유를 알려줘."
                response = model.generate_content(prompt)
                
                # 결과 출력
                st.success("✅ 추천 결과:")
                st.write(response.text)
                
            except Exception as e:
                if "429" in str(e):
                    st.error("오늘 할당량이 끝났습니다. 내일 다시 시도하거나 새 API 키를 넣어주세요.")
                else:
                    st.error(f"오류 발생: {e}")

st.divider()
st.caption("제공: Gemini AI")
