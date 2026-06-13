import streamlit as st
import requests
import tempfile
import asyncio
import edge_tts
from moviepy.editor import *
from datetime import datetime
import os
import pickle
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

# ========== DIAGNOSTIC – REMOVE AFTER TESTING ==========
st.write("### 🔍 Secret diagnostic (remove later)")
all_keys = list(st.secrets.keys())
st.write("Secrets found:", all_keys)
if "GROK_API_KEY" in st.secrets:
    key_len = len(st.secrets["GROK_API_KEY"])
    st.write(f"GROK_API_KEY exists, length: {key_len}")
    if key_len == 0:
        st.error("GROK_API_KEY is present but empty! Please fill it.")
else:
    st.error("GROK_API_KEY NOT found in secrets!")
st.markdown("---")

# ========== LOAD API KEYS ==========
GROQ_API_KEY = st.secrets.get("GROK_API_KEY", "")  # Using the same secret name
PEXELS_API_KEY = st.secrets.get("PEXELS_API_KEY", "")
YOUTUBE_CLIENT_ID = st.secrets.get("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = st.secrets.get("YOUTUBE_CLIENT_SECRET", "")
REDIRECT_URI = st.secrets.get("REDIRECT_URI", "https://your-app.streamlit.app/oauth2callback")

if not GROQ_API_KEY:
    st.error("API key missing. Please add GROK_API_KEY to Streamlit secrets.")
    st.stop()

# ========== CUSTOM CSS (LIGHT BLUE THEME) ==========
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #e0f0ff 0%, #b8d9ff 100%);
        color: #1a2a3a;
    }
    .big-title {
        font-size: 3rem;
        font-weight: bold;
        color: #1e3c72;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #2a4a7a;
        margin-bottom: 1rem;
    }
    .stButton>button {
        background-color: #2c7be5;
        color: white;
        border-radius: 30px;
        font-weight: bold;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #1a5bbf;
    }
    .security-badge {
        background: white;
        border: 1px solid #2c7be5;
        border-radius: 30px;
        padding: 8px 15px;
        margin: 10px 0;
        text-align: center;
        color: #1e3c72;
        font-weight: bold;
        font-family: monospace;
    }
    [data-testid="stSidebar"] {
        background-color: #cce4ff !important;
    }
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
                        "redirect_uris": [REDIRECT_URI]
                    }
                },
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
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
youtube_description = st.text_area("YouTube Video Description", value="Generated automatically by Groq AI and Pexels clips.")
privacy = st.selectbox("YouTube Privacy Status", ["public", "unlisted", "private"])

if st.button("🚀 Generate & Upload to YouTube", use_container_width=True):
    if not GROQ_API_KEY:
        st.error("API key missing in secrets.")
    elif auto_post and (not YOUTUBE_CLIENT_ID or not YOUTUBE_CLIENT_SECRET):
        st.error("YouTube OAuth credentials missing.")
    else:
        # ---------- 1. Generate script with Groq (Llama 3.1) ----------
        with st.spinner("Generating script using Groq AI (Llama 3.1)..."):
            api_url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
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

        # ---------- 2. Voiceover ----------
        with st.spinner("Generating voiceover..."):
            voice = "en-US-JennyNeural"
            output_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            async def tts():
                comm = edge_tts.Communicate(script, voice)
                await comm.save(output_audio)
            asyncio.run(tts())
            st.success("Voiceover ready.")

        # ---------- 3. Pexels clips ----------
        video_clips = []
        if PEXELS_API_KEY:
            with st.spinner("Fetching stock clips from Pexels..."):
                headers_pex = {"Authorization": PEXELS_API_KEY}
                keywords = niche.split()[:3]
                search_term = " ".join(keywords)
                url = f"https://api.pexels.com/videos/search?query={search_term}&per_page=3"
                try:
                    resp = requests.get(url, headers=headers_pex, timeout=10)
                    if resp.status_code == 200:
                        for video in resp.json().get("videos", []):
                            video_files = video.get("video_files", [])
                            if video_files:
                                clip_url = video_files[0]["link"]
                                clip_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                                clip_resp = requests.get(clip_url, stream=True)
                                with open(clip_path, "wb") as f:
                                    for chunk in clip_resp.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                video_clips.append(clip_path)
                except:
                    st.warning("Pexels fetch failed. Using fallback.")
            if not video_clips:
                video_clips = [None]
        else:
            video_clips = [None]

        # ---------- 4. Assemble video ----------
        with st.spinner("Assembling video..."):
            audio_clip = AudioFileClip(output_audio)
            duration = audio_clip.duration
            clips = []
            for clip_path in video_clips:
                if clip_path is None:
                    txt = TextClip(script[:100], fontsize=24, color='white', font='Arial', size=(640,480))
                    txt = txt.set_duration(duration/len(video_clips) if video_clips else duration).set_position('center')
                    bg = ColorClip(size=(640,480), color=(0,0,0), duration=duration/len(video_clips) if video_clips else duration)
                    clip = CompositeVideoClip([bg, txt])
                else:
                    clip = VideoFileClip(clip_path).subclip(0, duration/len(video_clips)).resize((640,480))
                clips.append(clip)
            final_video = concatenate_videoclips(clips, method="compose")
            final_video = final_video.set_audio(audio_clip)
            output_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            final_video.write_videofile(output_video, fps=24, codec='libx264', audio_codec='aac')
            st.success("Video assembled.")
            st.video(output_video)

        # ---------- 5. Upload to YouTube ----------
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

        # ---------- 6. Download button ----------
        with open(output_video, "rb") as f:
            st.download_button("📥 Download Video", f, file_name=f"faceless_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
