import streamlit as st
from google import genai
from google.genai import types
import os
import json
import urllib.parse

try:
    # 로컬 환경변수(os.getenv)와 배포 서버(st.secrets)에서 키를 순차적으로 찾습니다.
    api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("Gemini API 키를 설정해주세요. (로컬: 환경변수 / 배포: Streamlit Secrets)")
    st.stop()
    
def get_recommendation(age: int, preferred_genre: str, language_choice: str):
    if not preferred_genre.strip():
        genre_prompt = "전 세계적으로 실시간 인기가 많은 (Popular trending) 곡"
    else:
        genre_prompt = preferred_genre
        
    if language_choice == "선택 안 함":
        language_instruction = "추천 이유를 언어에 구애받지 않고 가장 적절하다고 판단되는 언어(예: 한국어, 영어)로 작성해 주세요."
        output_language = "자유"
    else:
        language_instruction = f"추천 이유를 {language_choice}어로 간결하게 설명해 주세요."
        output_language = language_choice
    
    prompt = f"""
    당신은 전문 음악 큐레이터입니다. 
    다음 사용자의 정보를 분석하여, 음악 3곡을 추천하고 {language_instruction}
    
    응답은 반드시 아래 JSON 스키마를 따르는 하나의 JSON 오브젝트여야 합니다. 
    다른 설명이나 텍스트를 JSON 바깥에 포함하지 마세요.
    
    사용자 정보:
    - 나이: {age}세
    - 선호 음악: {genre_prompt}
    - 추천 언어: {output_language}
    
    JSON 스키마:
    {{
      "recommendations": [
        {{
          "title": "노래 제목",
          "artist": "아티스트 이름",
          "reason": "추천 이유"
        }}
      ]
    }}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7 
            )
        )
        
        raw_text = response.text.strip()
        if raw_text.startswith('```json'):
            raw_text = raw_text[7:].strip()
        if raw_text.endswith('```'):
            raw_text = raw_text[:-3].strip()

        return json.loads(raw_text)
        
    except json.JSONDecodeError:
        return {"error": "AI 응답 형식이 올바르지 않습니다. 다시 시도해주세요."}
    except Exception as e:
        return {"error": f"API 호출 오류: {e}"}

st.set_page_config(page_title="🎶 AI 음악 추천 시스템", layout="centered")
st.title("🎵 개인화된 음악 추천 AI")
st.markdown("나이와 선호 장르를 입력하고 추천 언어를 선택하세요.")

with st.form("recommendation_form"):
    age = st.number_input("나이를 입력해 주세요:", min_value=1, max_value=100, value=25, step=1)
    genre = st.text_input("선호하는 음악 장르를 입력해 주세요 (빈 칸은 실시간 인기곡 추천):", value="")
    
    language_full_list = ['선택 안 함', 'Korean', 'English', 'Japanese', 'Chinese']
    language_display = {
        'Korean': 'Korean (한국어)', 
        'English': 'English (영어)', 
        'Japanese': 'Japanese (일본어)', 
        'Chinese': 'Chinese (중국어)',
        '선택 안 함': '선택 안 함'
    }
    
    selected_language_key = st.selectbox(
        "추천 결과를 보고 싶은 언어를 선택하세요:",
        options=language_full_list,
        format_func=lambda x: language_display[x]
    )
    
    submitted = st.form_submit_button("음악 추천받기 🌟")

if submitted:
    with st.spinner("Gemini가 당신의 취향을 분석하고 음악을 고르는 중입니다..."):
        recommendation_data = get_recommendation(age, genre, selected_language_key)
        
        if "error" in recommendation_data:
            st.error(recommendation_data["error"])
        else:
            st.success("✅ 추천 완료!")
            if not genre.strip():
                st.subheader("🔥 실시간 인기곡 기반 음악 추천 결과:")
            else:
                st.subheader("🎧 당신을 위한 음악 추천 결과:")
                
            for i, rec in enumerate(recommendation_data.get("recommendations", [])):
                title = rec.get("title", "제목 없음")
                artist = rec.get("artist", "아티스트 정보 없음")
                reason = rec.get("reason", "추천 이유 없음")
                
                search_query = f"{title} {artist}"
                encoded_query = urllib.parse.quote_plus(search_query)
                youtube_link = f"https://www.youtube.com/results?search_query={encoded_query}"
                
                st.markdown(f"**{i+1}. {title}** (by **{artist}**)")
                st.markdown(f"**추천 이유**: {reason}")
                st.markdown(f"[▶️ **YouTube에서 음악 듣기**]({youtube_link})")
                st.markdown("---")
