import streamlit as st
from openai import OpenAI
import json
import urllib.parse

# 1. API 설정 (DeepSeek 기반)
try:
    api_key = st.secrets.get("DEEPSEEK_API_KEY")
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
except Exception:
    st.error("DeepSeek API 키 설정을 확인해주세요 (Secrets 내 DEEPSEEK_API_KEY).")
    st.stop()

# 2. 세션 상태 초기화 (추천 기록 및 탐색 인덱스)
if "history" not in st.session_state:
    st.session_state.history = []
if "index" not in st.session_state:
    st.session_state.index = -1

def get_recommendation(user_age, preferred_genre):
    # 중복 추천 방지를 위해 최근 기록 추출
    past_songs = [rec['title'] for h in st.session_state.history for rec in h.get('recommendations', [])]
    past_songs_str = ", ".join(past_songs[-20:]) 

    # [프롬프트 수정] 장르 분류의 엄격함과 최신성(2020-2025) 강화
    prompt = f"""
    당신은 음악 장르 분류 및 큐레이션 전문가입니다. {user_age}세 사용자에게 '{preferred_genre}' 장르의 음악 3곡을 추천하세요.
    
    [장르 판별 엄격 기준]
    1. **장르 일치성**: 선택된 장르({preferred_genre})의 핵심 요소가 없는 곡은 절대 제외하세요.
       - 힙합/랩: 반드시 래핑이 포함되어야 하며, 강한 비트나 808 베이스가 중심인 곡 (BTS의 Dynamite 같은 디스코 팝은 힙합 제외).
       - 발라드: 느린 템포, 서정적인 보컬, 피아노/스트링 중심의 감성적인 곡.
       - K-POP/댄스: 화려한 퍼포먼스와 빠른 비트의 댄스 팝.
    2. **시대 제한**: 반드시 2020년부터 2025년 사이에 실제 발매된 곡만 선정하세요.
    3. **중복 금지**: 이전에 추천한 [{past_songs_str}]는 제외하세요.
    4. **한국어 전용**: 추천 사유는 반드시 한국어로 작성하고, 왜 이 곡이 해당 장르에 부합하는지 기술적으로 설명하세요.
    
    JSON 형식:
    {{
      "recommendations": [
        {{ 
          "title": "실제 곡 제목", 
          "artist": "실제 아티스트", 
          "genre_detail": "정확한 세부 장르(예: 붐뱁 힙합, 팝 발라드)", 
          "reason": "해당 장르의 특징을 포함한 한국어 추천 사유" 
        }}
      ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a precise music curator who classifies genres strictly. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.3 # 정확도를 위해 낮게 설정
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

# --- UI 레이아웃 ---
st.set_page_config(page_title="AI 장르 정밀 큐레이터", page_icon="🎵")
st.title("🎵 장르 정밀 매칭 음악 추천 (2020-2025)")
st.write("사용자가 선택한 장르의 특징을 정확히 분석하여 최신곡 위주로 추천합니다.")

# 사이드바 입력
with st.sidebar:
    st.header("설정")
    age = st.number_input("나이:", 1, 100, 25)
    genre_choice = st.selectbox("추천받을 장르:", 
                                ["힙합/랩", "발라드", "K-POP/댄스", "R&B/소울", "인디/록"])
    extra = st.text_input("추가 희망사항 (가수명 등):", placeholder="예: 박재범, 슬픈 노래")
    
    target_genre = f"{genre_choice} ({extra})" if extra else genre_choice

# 새로운 추천 생성 버튼
if st.button("새로운 장르 추천 받기 🚀", use_container_width=True):
    with st.spinner(f"'{genre_choice}' 장르 데이터를 분석 중..."):
        new_res = get_recommendation(age, target_genre)
        if "error" not in new_res:
            st.session_state.history.append(new_res)
            st.session_state.index = len(st.session_state.history) - 1
        else:
            st.error("API 연동에 문제가 발생했습니다.")

# --- 히스토리 내비게이션 UI (화살표 기능) ---
if st.session_state.history:
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ 이전 결과", disabled=(st.session_state.index <= 0)):
            st.session_state.index -= 1
            st.rerun()
    with col2:
        st.write(f"<center><b>{st.session_state.index + 1} / {len(st.session_state.history)}</b></center>", unsafe_allow_html=True)
    with col3:
        if st.button("다음 결과 ➡️", disabled=(st.session_state.index >= len(st.session_state.history) - 1)):
            st.session_state.index += 1
            st.rerun()

    # 현재 기록 표시
    current_view = st.session_state.history[st.session_state.index]
    
    for i, rec in enumerate(current_view.get("recommendations", [])):
        with st.container(border=True):
            st.subheader(f"{i+1}. {rec['title']} - {rec['artist']}")
            st.caption(f"📌 세부 분류: {rec.get('genre_detail', '음악')}")
            st.info(f"💡 **이유**: {rec['reason']}")
            
            # 유튜브 링크
            q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
            st.link_button("▶️ 유튜브 검색", f"https://www.youtube.com/results?search_query={q}")
