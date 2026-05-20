import streamlit as st
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import json

# 1. 세션 상태 초기화
if "poster_image" not in st.session_state:
    st.session_state.poster_image = None
if "recommendations" not in st.session_state:
    st.session_state.recommendations = None

# 스트림릿 페이지 설정
st.set_page_config(page_title="인생의 사운드트랙 (Life OST)", page_icon="🎬", layout="centered")

st.title("🎬 인생의 사운드트랙 (Life-Movie OST)")
st.subheader("오늘 당신의 하루를 영화로 만든다면 어울릴 OST는?")
st.write("오늘 있었던 일이나 감정을 한두 줄로 적어주세요. AI가 당신만을 위한 영화 포스터와 OST를 선물합니다.")

# 사이드바 - API 키 입력
with st.sidebar:
    st.header("설정")
    api_key = st.text_input("OpenAI API Key를 입력하세요", type="password")
    st.markdown("[OpenAI API Key 발급받기](https://platform.openai.com/api-keys)")

# 메인 입력창
user_diary = st.text_area("✍️ 오늘의 일기 (한두 줄로 자유롭게 적어보세요)", placeholder="예: 오늘 중요한 미팅이 끝났다. 시원섭섭하지만 홀가분하다. 퇴근길 노을이 예쁘네.")

# 포스터에 사용할 감성 배경 테마 선택
theme_color = st.selectbox("🎨 포스터의 감성 테마 선택", ["새벽 감성 (Dark blue)", "따뜻한 위로 (Warm Beige)", "오늘의 열정 (Sunset Red)", "차분한 하루 (Minimal Gray)"])

# 테마별 색상 정의
color_map = {
    "새벽 감성 (Dark blue)": (20, 24, 45),
    "따뜻한 위로 (Warm Beige)": (245, 242, 235),
    "오늘의 열정 (Sunset Red)": (64, 25, 25),
    "차분한 하루 (Minimal Gray)": (240, 240, 240)
}
text_color_map = {
    "새벽 감성 (Dark blue)": (255, 255, 255),
    "따뜻한 위로 (Warm Beige)": (40, 40, 40),
    "오늘의 열정 (Sunset Red)": (255, 230, 230),
    "차분한 하루 (Minimal Gray)": (50, 50, 50)
}

# --- 로직 함수들 ---

def analyze_and_recommend(diary_text, client):
    """일기를 분석하여 감정 태그, 영화 제목, 추천 OST 3곡을 반환합니다."""
    
    # f-string 오류를 근본적으로 차단하기 위해 일반 멀티라인 문자열과 replace 방식을 사용합니다.
    prompt_template = """
    사용자가 쓴 오늘 하루의 일기입니다:
    "{DIARY_TEXT}"
    
    이 일기의 감정선을 분석해서 다음 정보를 포함한 JSON 형태로만 응답해주세요.
    마크다운 블록(```json ...)은 절대 사용하지 마세요.
    
    Required JSON Format:
    {
        "emotion_tag": "분석된 핵심 감정 단어 하나 (예: 홀가분함, 쓸쓸함)",
        "movie_title": "이 하루를 영화로 만든다면 어울릴 가상의 영화 제목",
        "ost_list": [
            {"title": "곡 제목 1", "artist": "아티스트 1", "reason": "위로의 한마디"},
            {"title": "곡 제목 2", "artist": "아티스트 2", "reason": "위로의 한마디"},
            {"title": "곡 제목 3", "artist": "아티스트 3", "reason": "위로의 한마디"}
        ]
    }
    """
    
    # 템플릿 안의 치환자를 사용자의 일기 텍스트로 변경합니다.
    prompt = prompt_template.replace("{DIARY_TEXT}", diary_text)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a warm, empathetic movie critic and music therapist. Always respond in Korean and strictly match the JSON format requested."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

def create_poster(movie_title, emotion_tag, ost_list, bg_color, text_color):
    """Pillow를 활용하여 영화 포스터 스타일 템플릿을 생성합니다."""
    img = Image.new("RGB", (800, 1200), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("NanumMyeongjo.ttf", 55)
        font_subtitle = ImageFont.truetype("NanumMyeongjo.ttf", 28)
        font_body = ImageFont.truetype("NanumMyeongjo.ttf", 22)
    except IOError:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_body = ImageFont.load_default()

    # 상단 텍스트
    draw.text((400, 150), f"A FILM OF TODAY'S EMOTION : {emotion_tag}", fill=text_color, font=font_subtitle, anchor="mm")
    
    # 구분선
    draw.line([(200, 200), (600, 200)], fill=text_color, width=2)
    
    # 중앙 영화 제목
    draw.text((400, 450), f"〈 {movie_title} 〉", fill=text_color, font=font_title, anchor="mm")
    
    # 하단 크레딧 섹션
    draw.text((400, 750), "SOUNDTRACK OF MY LIFE", fill=text_color, font=font_subtitle, anchor="mm")
    draw.line([(300, 790), (500, 790)], fill=text_color, width=1)
    
    y_offset = 850
    for i, ost in enumerate(ost_list):
        ost_text = f"{i+1}. {ost['title']} - {ost['artist']}"
        draw.text((400, y_offset), ost_text, fill=text_color, font=font_body, anchor="mm")
        y_offset += 60

    # 하단 스튜디오 로고 명시
    draw.text((400, 1100), "Life-Movie OST AI Studio", fill=text_color, font=font_body, anchor="mm")
    
    return img

# --- 실행 버튼 ---
if st.button("내 하루의 OST 찾기 🎵"):
    if not api_key:
        st.warning("오른쪽 사이드바에 OpenAI API Key를 입력해주세요!")
    elif not user_diary.strip():
        st.warning("오늘의 일기를 한 줄 이상 작성해주세요!")
    else:
        with st.spinner("당신의 하루를 영화로 제작 중입니다... 🎬"):
            try:
                # 1. AI 분석 및 추천
                client = OpenAI(api_key=api_key)
                res_data = analyze_and_recommend(user_diary, client)
                st.session_state.recommendations = res_data
                
                # 2. 이미지 포스터 생성
                bg_color = color_map[theme_color]
                text_color = text_color_map[theme_color]
                
                poster_img = create_poster(
                    movie_title=res_data["movie_title"],
                    emotion_tag=res_data["emotion_tag"],
                    ost_list=res_data["ost_list"],
                    bg_color=bg_color,
                    text_color=text_color
                )
                st.session_state.poster_image = poster_img
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")

# --- 결과 출력 ---
if st.session_state.recommendations and st.session_state.poster_image:
    st.success("✨ 당신의 오늘 하루가 영화로 재탄생했습니다!")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader(f"🎬 영화 제목: {st.session_state.recommendations['movie_title']}")
        st.caption(f"오늘의 감정 테마: {st.session_state.recommendations['emotion_tag']}")
        st.write("---")
        
        st.markdown("### 🎵 추천 사운드트랙")
        for i, ost in enumerate(st.session_state.recommendations['ost_list']):
            st.markdown(f"**{i+1}. {ost['title']}** - {ost['artist']}")
            st.caption(f"💡 *{ost['reason']}*")
            st.write("")
            
    with col2:
        st.markdown("### 📸 SNS 공유용 포스터")
        st.image(st.session_state.poster_image, use_container_width=True)
        
        # 이미지 다운로드 버튼 빌드
        buf = BytesIO()
        st.session_state.poster_image.save(buf, format="PNG")
        byte_im = buf.getvalue()
        
        st.download_button(
            label="🖼️ 포스터 이미지 다운로드",
            data=byte_im,
            file_name=f"life_ost_{st.session_state.recommendations['movie_title']}.png",
            mime="image/png"
        )
