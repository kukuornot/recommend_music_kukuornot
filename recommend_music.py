import streamlit as st
from openai import OpenAI
import json
import urllib.parse

# 1. API 설정 (DeepSeek 기반)
try:
    api_key = st.secrets.get("DEEPSEEK_API_KEY")
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
except Exception:
    st.error("DeepSeek API 키 설정을 확인해주세요.")
    st.stop()

# 2. 세션 상태 초기화 (히스토리 관리용)
if "history" not in st.session_state:
    st.session_state.history = []
if "index" not in st.session_state:
    st.session_state.index = -1

def get_recommendation(user_age, preferred_genre):
    # 중복 추천 방지 리스트 생성
    past_songs = [rec['title'] for h in st.session_state.history for rec in h.get('recommendations', [])]
    past_songs_str = ", ".join(past_songs[-20:]) 

    # [프롬프트 수정] 장르 정밀도 및 최신성(2020-2025) 강화
    prompt = f"""
    당신은 음악 장르 분석 전문가입니다. {user_age}세 사용자를 위해 '{preferred_genre}' 장르의 음악 3곡을 추천하세요.
    
    [엄격한 규칙]
    1. **시대 제한**: 반드시 2020년부터 2025년 사이에 발표된 곡만 추천하세요. 2020년 이전 곡은 절대 금지입니다.
    2. **장르 정밀도**: 사용자가 선택한 장르({preferred_genre})의 음악적 특징(발라드-감성/보컬, 힙합-비트/래핑, 댄스-템포/퍼포먼스)을 정확히 반영한 곡이어야 합니다.
    3. **중복 금지**: 다음 곡들은 제외하세요: [{past_songs_str}]
    4. **한국어 전용**: 추천 사유(reason)는 전문적인 음악 용어를 섞어 반드시 한국어로만 작성하세요.
    
    반드시 아래 JSON 형식으로만 답변하세요:
    {{
      "recommendations": [
        {{ 
          "title": "실제 곡 제목", 
          "artist": "실제 아티스트", 
          "genre_detail": "정확한 세부 장르(예: 트랩 힙합, 알앤비 발라드)", 
          "reason": "해당 장르적 특징과 추천 이유" 
        }}
      ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a precise music genre classifier. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.4 # 장르 정확도를 위해 창의성 수치를 낮춤
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

# --- UI 레이아웃 ---
st.set_page_config(page_title="장르별 음악 큐레이터", page_icon="🎵")
st.title("🎵 장르 정밀 매칭 음악 추천")
st.write("2020-2025년 최신곡 중 사용자의 선호 장르를 정확히 분석하여 추천합니다.")

# 사이드바 입력창
with st.sidebar:
    st.header("설정")
    age = st.number_input("나이:", 1, 100, 25)
    # 장르를 명확히 선택하게 하여 정확도를 높임
    genre_choice = st.selectbox("추천받을 장르:", 
                                ["K-POP/댄스", "발라드", "힙합/랩", "R&B/소울", "인디/록"])
    user_input = st.text_input("추가 희망사항 (가수 등):", placeholder="예: 신나는 분위기")
    
    combined_genre = f"{genre_choice} ({user_input})" if user_input else genre_choice

# 새로운 추천 실행
if st.button("전문 AI 장르 추천 받기 ✨", use_container_width=True):
    with st.spinner(f"'{genre_choice}' 카테고리 분석 중..."):
        new_res = get_recommendation(age, combined_genre)
        if "error" not in new_res:
            st.session_state.history.append(new_res)
            st.session_state.index = len(st.session_state.history) - 1
        else:
            st.error("API 호출 중 오류가 발생했습니다.")

# --- 히스토리 탐색 컨트롤러 ---
if st.session_state.history:
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ 이전 추천", disabled=(st.session_state.index <= 0)):
            st.session_state.index -= 1
            st.rerun()
    with col2:
        st.write(f"<center><b>결과 {st.session_state.index + 1} / {len(st.session_state.history)}</b></center>", unsafe_allow_html=True)
    with col3:
        if st.button("다음 추천 ➡️", disabled=(st.session_state.index >= len(st.session_state.history) - 1)):
            st.session_state.index += 1
            st.rerun()

    # 현재 기록 출력
    current_data = st.session_state.history[st.session_state.index]
    
    for rec in current_data.get("recommendations", []):
        with st.container(border=True):
            st.subheader(f"{rec['title']} - {rec['artist']}")
            st.caption(f"📌 세부 장르: {rec.get('genre_detail', '음악')}")
            st.write(f"💬 {rec['reason']}")
            
            # 유튜브 링크
            q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
            st.link_button("▶️ 유튜브 검색 결과 확인", f"https://www.youtube.com/results?search_query={q}")
