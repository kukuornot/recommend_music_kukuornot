import streamlit as st
from openai import OpenAI
import json
import urllib.parse

# 1. API 설정 (DeepSeek 기반)
try:
    api_key = st.secrets.get("DEEPSEEK_API_KEY")
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
except Exception:
    st.error("API 키 설정을 확인해주세요.")
    st.stop()

# 2. 히스토리 관리를 위한 세션 상태
if "history" not in st.session_state:
    st.session_state.history = []
if "index" not in st.session_state:
    st.session_state.index = -1

def get_recommendation(user_age, preferred_genre):
    # 중복 추천 방지 로직
    past_songs = [rec['title'] for h in st.session_state.history for rec in h.get('recommendations', [])]
    past_songs_str = ", ".join(past_songs[-15:]) 

    # [수정] 최신곡 제한을 풀고 '음악적 가치'에 집중한 프롬프트
    prompt = f"""
    당신은 전 시대를 아우르는 음악 박사입니다. {user_age}세 사용자에게 '{preferred_genre}'와 관련된 최고의 음악 3곡을 추천하세요.
    
    [가이드라인]
    1. **시대 무관**: 90년대 명곡, 2010년대 인디, 혹은 아주 최근의 노래까지 모두 가능합니다.
    2. **취향 저격**: 사용자의 나이대({user_age}세)를 고려하여 추억을 자극하거나 새로움을 줄 수 있는 곡을 선정하세요.
    3. **중복 금지**: [{past_songs_str}]에 포함된 곡은 제외하세요.
    4. **한국어 설명**: 추천 이유는 반드시 한국어로, 전문적이고 감성적으로 작성하세요.
    
    JSON 형식:
    {{
      "recommendations": [
        {{ "title": "곡 제목", "artist": "아티스트", "reason": "이 곡이 선정된 이유와 감상 포인트" }}
      ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a legendary music curator who knows all eras. Output JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.8 # 더 창의적이고 다양한 시대의 곡을 위해 온도를 높임
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

# --- UI 섹션 ---
st.set_page_config(page_title="올타임 음악 큐레이터", page_icon="🎷")
st.title("🎷 올타임 인생곡 큐레이션")
st.write("시대를 불문하고 당신의 마음에 닿을 최고의 음악을 찾아드립니다.")

# 입력부
with st.sidebar:
    st.header("사용자 프로필")
    age = st.number_input("나이:", 1, 100, 25)
    genre = st.text_input("분위기/장르/아티스트:", placeholder="예: 비 오는 날 듣기 좋은, 올드스쿨 힙합, 유재하")

# 새로운 추천 생성
if st.button("음악 탐험 시작하기 🚀", use_container_width=True):
    with st.spinner("당신을 위한 명곡을 선별 중..."):
        new_res = get_recommendation(age, genre)
        if "error" not in new_res:
            st.session_state.history.append(new_res)
            st.session_state.index = len(st.session_state.history) - 1
        else:
            st.error("추천에 실패했습니다.")

# --- 히스토리 내비게이션 ---
if st.session_state.history:
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ 이전 기록", disabled=(st.session_state.index <= 0)):
            st.session_state.index -= 1
            st.rerun()
    with col2:
        st.write(f"<center>{st.session_state.index + 1} / {len(st.session_state.history)}</center>", unsafe_allow_html=True)
    with col3:
        if st.button("다음 기록 ➡️", disabled=(st.session_state.index >= len(st.session_state.history) - 1)):
            st.session_state.index += 1
            st.rerun()

    current_res = st.session_state.history[st.session_state.index]
    
    for i, rec in enumerate(current_res.get("recommendations", [])):
        with st.container(border=True):
            st.subheader(f"{rec['title']} - {rec['artist']}")
            st.write(f"📖 {rec['reason']}")
            
            # 검색 및 감상 링크
            q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
            st.link_button("🎵 유튜브에서 감상하기", f"https://www.youtube.com/results?search_query={q}")
