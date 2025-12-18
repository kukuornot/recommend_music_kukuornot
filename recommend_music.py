import streamlit as st
from openai import OpenAI
import json
import urllib.parse

# 1. API 설정 (DeepSeek)
try:
    api_key = st.secrets.get("DEEPSEEK_API_KEY")
    client = OpenAI(
        api_key=api_key, 
        base_url="https://api.deepseek.com"
    )
except Exception:
    st.error("DeepSeek API 키가 설정되지 않았습니다. Secrets를 확인해주세요.")
    st.stop()

# 2. 세션 상태 초기화 (히스토리 및 인덱스)
if "history" not in st.session_state:
    st.session_state.history = []
if "index" not in st.session_state:
    st.session_state.index = -1

def get_recommendation(user_age, genre_choice):
    # 중복 방지를 위한 최근 곡 목록
    past_songs = [rec['title'] for h in st.session_state.history for rec in h.get('recommendations', [])]
    past_songs_str = ", ".join(past_songs[-15:])

    # [프롬프트 수정] 논리적 모순 방지 및 장르 엄격 격리
    prompt = f"""
    당신은 음악 장르 판별 전문가입니다. {user_age}세 사용자에게 '{genre_choice}' 장르 3곡을 추천하세요.
    
    [절대 준수 규칙]
    1. **논리적 일관성**: 장르에 맞지 않는 곡(예: 힙합 카테고리의 Dynamite, Hype Boy 등)은 분석글에 쓰지도 말고 리스트에서 아예 제외하세요.
    2. **장르 정의**: 
       - 힙합/랩: 반드시 래핑이 곡의 80% 이상인 곡만 선정.
       - 발라드: 2020년 이후 발매된 서정적인 곡.
    3. **팩트 체크**: 곡 제목과 아티스트가 실제와 일치하는지 3번 검토하세요. (예: 'Hmm'은 BE'O의 곡)
    4. **최신성**: 2020~2025년 사이 발표된 실제 곡만 선정.
    5. **중복 금지**: 다음 곡 제외: [{past_songs_str}]
    
    반드시 아래 JSON 형식으로만 답변하세요:
    {{
      "recommendations": [
        {{ "title": "실제 곡 제목", "artist": "실제 아티스트", "reason": "장르적 특징을 근거로 한 한국어 설명" }}
      ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a professional music curator. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.1  # 환각 방지를 위해 낮게 설정
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        # 잔액 부족 시 사용자에게 알림
        if "insufficient balance" in str(e).lower() or "402" in str(e):
            return {"error": "DeepSeek 계정의 잔액이 부족합니다. ($2 정도 충전을 권장합니다)"}
        return {"error": f"API 오류: {str(e)}"}

# --- UI 레이아웃 ---
st.set_page_config(page_title="맞춤형 음악 추천", page_icon="🎯")
st.title("🎯 AI 기반 맞춤형 음악 추천")
st.write("AI의 오류로 버그나 정보의 불일치가 있을수도 있습니다.")

with st.sidebar:
    st.header("설정")
    age = st.number_input("나이:", 1, 100, 25)
    genre = st.selectbox("장르 선택:", ["힙합/랩", "발라드", "K-POP/댄스", "R&B/소울"])
    extra = st.text_input("추가 희망사항:", placeholder="예: 비트가 강한, 슬픈")

if st.button("전문 AI 추천 받기 🚀", use_container_width=True):
    with st.spinner("데이터 검증 중..."):
        res = get_recommendation(age, f"{genre} {extra}")
        if "error" in res:
            st.error(res["error"])
        else:
            st.session_state.history.append(res)
            st.session_state.index = len(st.session_state.history) - 1

# --- 결과 및 히스토리 내비게이션 ---
if st.session_state.history:
    st.divider()
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("⬅️ 이전", disabled=(st.session_state.index <= 0)):
            st.session_state.index -= 1
            st.rerun()
    with c2:
        st.write(f"<center><b>{st.session_state.index + 1} / {len(st.session_state.history)}</b></center>", unsafe_allow_html=True)
    with c3:
        if st.button("다음 ➡️", disabled=(st.session_state.index >= len(st.session_state.history) - 1)):
            st.session_state.index += 1
            st.rerun()

    current_data = st.session_state.history[st.session_state.index]
    for i, rec in enumerate(current_data.get("recommendations", [])):
        with st.container(border=True):
            st.subheader(f"{i+1}. {rec['title']} - {rec['artist']}")
            st.info(f"📑 **분석**: {rec['reason']}")
            q = urllib.parse.quote(f"{rec['title']} {rec['artist']}")
            st.link_button("▶️ 유튜브 확인", f"https://www.youtube.com/results?search_query={q}")

