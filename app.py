import streamlit as st
import requests
import tempfile
import os
import pickle
import numpy as np
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import *
from gtts import gTTS
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="Faceless Video Automator | Groq AI",
    page_icon="🎬",
    layout="wide"
)

# ========== LOAD API KEYS ==========
GROQ_API_KEY = st.secrets.get("GROK_API_KEY", "")
YOUTUBE_CLIENT_ID = st.secrets.get("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = st.secrets.get("YOUTUBE_CLIENT_SECRET", "")
REDIRECT_URI = st.secrets.get("REDIRECT_URI", "https://your-app.streamlit.app")

if not GROQ_API_KEY:
    st.error("GROK_API_KEY (Groq key) is missing. Please add it to Streamlit secrets.")
    st.stop()

# ========== CUSTOM CSS ==========
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #e0f0ff 0%, #b8d9ff 100%); color: #1a2a3a; }
    .big-title { font-size: 3rem; font-weight: bold; color: #1e3c72; margin-bottom: 0.2rem; }
    .subtitle { font-size: 1.2rem; color: #2a4a7a; margin-bottom: 1rem; }
    .stButton>button { background-color: #2c7be5; color: white; border-radius: 30px; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #1a5bbf; }
    .security-badge { background: white; border: 1px solid #2c7be5; border-radius: 30px; padding: 8px 15px; text-align: center; color: #1e3c72; font-weight: bold; }
    [data-testid="stSidebar"] { background-color: #cce4ff !important; }
</style>
""", unsafe_allow_html=True)

# ========== SIDEBAR ==========
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/null/youtube-play.png", width=80)
    st.markdown("## **Faceless Video Automator**")
    st.markdown("Powered by **Groq AI (Llama 3.1)**")
    st.markdown("---")
    st.markdown("### 🛡️ Global Security Shield")
    st.markdown(f'<div class="security-badge">🔐 Secure API connection active</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("Built by **Gesner Deslandes**, Engineer-in-Chief")
    st.markdown("📞 (509) 4738 5663")
    st.markdown("✉️ deslandes78@gmail.com")
    st.markdown("🌐 [GlobalInternet.py](https://globalinternetsitepy-abh7v6tnmskxxnuplrdcgk.streamlit.app/)")
    st.markdown("---")
    st.caption("© 2026 GlobalInternet.py")

# ========== YOUTUBE OAUTH ==========
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def get_youtube_service():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": YOUTUBE_CLIENT_ID,
                        "client_secret": YOUTUBE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [REDIRECT_URI + "/oauth2callback"]
                    }
                },
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI + "/oauth2callback"
            )
            auth_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
            st.session_state['oauth_state'] = state
            st.info("YouTube authentication required. Click the link below to authorize.")
            st.markdown(f"[Authorize YouTube Upload]({auth_url})")
            st.markdown("After granting permission, you will be redirected back.")
            query_params = st.query_params
            if "code" in query_params:
                code = query_params["code"]
                flow.fetch_token(code=code)
                creds = flow.credentials
                with open("token.pickle", "wb") as token:
                    pickle.dump(creds, token)
                st.success("YouTube authentication successful!")
                st.rerun()
            else:
                st.stop()
    return build("youtube", "v3", credentials=creds)

def upload_to_youtube(video_path, title, description, category_id="22", privacy_status="public"):
    youtube = get_youtube_service()
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["faceless", "AI", "automated"],
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status
        }
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    return response

# ========== CREATE TEXT CLIP (Pillow 10 compatible) ==========
def create_text_clip(text, duration, size=(640,480), fontsize=24):
    img = Image.new('RGB', size, color='black')
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize)
    except:
        font = ImageFont.load_default()
    # Wrap text
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + word + " "
        bbox = draw.textbbox((0,0), test_line, font=font)
        if bbox[2] - bbox[0] <= size[0] - 20:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + " "
    if current_line:
        lines.append(current_line)
    line_height = fontsize + 6
    total_height = len(lines) * line_height
    y = (size[1] - total_height) // 2
    for line in lines:
        draw.text((10, y), line, fill='white', font=font)
        y += line_height
    img_array = np.array(img)
    clip = ImageClip(img_array, duration=duration)
    return clip

# ========== MAIN UI ==========
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown('<div class="big-title">🎬 Faceless Video Automator with Groq AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Generate and auto-post faceless videos daily using AI.</div>', unsafe_allow_html=True)
with col2:
    st.image(
        "https://raw.githubusercontent.com/Deslandes1/Generate-faceless-videos/main/Gesner%20Deslandes.png",
        width=120,
        caption="Gesner Deslandes"
    )

niche = st.text_input("Enter your video niche (e.g., motivation, history, technology)", value="motivation")
style = st.selectbox("Choose video style", ["Dynamic", "Calm", "Inspirational", "Educational"])
auto_post = st.checkbox("Auto‑post to YouTube (requires OAuth)")
youtube_title = st.text_input("YouTube Video Title", value=f"Faceless Video - {datetime.now().strftime('%Y%m%d')}")
youtube_description = st.text_area("YouTube Video Description", value="Generated automatically by Groq AI and gTTS voice. Text overlay by GlobalInternet.py.")
privacy = st.selectbox("YouTube Privacy Status", ["public", "unlisted", "private"])

if st.button("🚀 Generate & Upload to YouTube", use_container_width=True):
    if not GROQ_API_KEY:
        st.error("Groq API key missing in secrets.")
    elif auto_post and (not YOUTUBE_CLIENT_ID or not YOUTUBE_CLIENT_SECRET):
        st.error("YouTube OAuth credentials missing.")
    else:
        # ---------- 1. Generate script with Groq ----------
        with st.spinner("Generating script using Groq AI..."):
            api_url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            prompt = f"Write a short, engaging script for a faceless video in the {niche} niche. Style: {style}. Keep it under 200 words."
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 300
            }
            try:
                response = requests.post(api_url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                script = response.json()["choices"][0]["message"]["content"]
                st.success("Script generated!")
                st.text_area("Generated Script", script, height=150)
            except Exception as e:
                st.error(f"Groq API error: {e}")
                st.stop()

        # ---------- 2. Generate voice using gTTS (no 403 errors) ----------
        with st.spinner("Generating voice using gTTS..."):
            output_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            try:
                # gTTS supports English, French, Spanish. Map language.
                lang_map = {"English": "en", "French": "fr", "Spanish": "es"}
                tts = gTTS(text=script, lang=lang_map.get(style, "en"), slow=False)
                tts.save(output_audio)
                st.success("Voiceover ready.")
                voice_success = True
            except Exception as e:
                st.warning(f"gTTS failed: {e}. Creating silent audio.")
                # silent audio
                silent = AudioClip(lambda t: 0, duration=10, fps=44100)
                silent.write_audiofile(output_audio, codec='libmp3lame', verbose=False, logger=None)
                silent.close()
                voice_success = False

        # ---------- 3. Create video clips (black with text overlay) ----------
        with st.spinner("Creating video..."):
            audio_clip = AudioFileClip(output_audio)
            duration = audio_clip.duration
            # Split script into 3 segments for variation
            script_parts = [script[:len(script)//3], script[len(script)//3:2*len(script)//3], script[2*len(script)//3:]]
            per_clip_duration = duration / 3
            clips = []
            for i, part in enumerate(script_parts):
                if not part.strip():
                    part = script[:100]
                clip = create_text_clip(part, duration=per_clip_duration, size=(640,480), fontsize=24)
                clips.append(clip)
            final_video = concatenate_videoclips(clips, method="compose")
            final_video = final_video.set_audio(audio_clip)
            output_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            final_video.write_videofile(output_video, fps=24, codec='libx264', audio_codec='aac')
            st.success("Video assembled.")
            st.video(output_video)

        # ---------- 4. Upload to YouTube ----------
        if auto_post:
            with st.spinner("Uploading to YouTube..."):
                try:
                    result = upload_to_youtube(output_video, youtube_title, youtube_description, privacy_status=privacy)
                    video_url = f"https://www.youtube.com/watch?v={result['id']}"
                    st.success(f"Uploaded! [Watch on YouTube]({video_url})")
                except Exception as e:
                    st.error(f"YouTube upload failed: {e}")
        else:
            st.info("Auto‑upload disabled. Download video below.")

        # ---------- 5. Download button ----------
        with open(output_video, "rb") as f:
            st.download_button("📥 Download Video", f, file_name=f"faceless_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
