import streamlit as st
import requests
import tempfile
import asyncio
import edge_tts
from moviepy.editor import *
from datetime import datetime
import os
import pickle
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="Faceless Video Automator | Grok AI",
    page_icon="🎬",
    layout="wide"
)

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

# ========== LOAD API KEYS FROM STREAMLIT SECRETS ==========
def get_secret(key, default=""):
    try:
        return st.secrets[key]
    except:
        return default

GROK_API_KEY = get_secret("GROK_API_KEY")
PEXELS_API_KEY = get_secret("PEXELS_API_KEY")
YOUTUBE_CLIENT_ID = get_secret("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = get_secret("YOUTUBE_CLIENT_SECRET")

# ========== SIDEBAR INFO ==========
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/null/youtube-play.png", width=80)
    st.markdown("## **Faceless Video Automator**")
    st.markdown("Powered by **Grok AI (xAI)**")
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

# ========== YOUTUBE OAUTH SETUP ==========
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
REDIRECT_URI = st.secrets.get("REDIRECT_URI", "https://your-app.streamlit.app/oauth2callback")

def get_authenticated_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use the client ID and secret from secrets to build flow
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
            # Get the authorization URL
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            st.session_state['oauth_state'] = state
            st.info("Please click the link below to authorize YouTube uploads.")
            st.markdown(f"[Authorize YouTube Upload]({auth_url})")
            # Wait for callback
            query_params = st.query_params
            if "code" in query_params:
                code = query_params["code"]
                flow.fetch_token(code=code)
                creds = flow.credentials
                # Save credentials for next run
                with open("token.pickle", "wb") as token:
                    pickle.dump(creds, token)
                st.success("Authentication successful! You can now upload videos.")
                st.rerun()
            else:
                st.stop()
    return build("youtube", "v3", credentials=creds)

# ========== FUNCTION TO UPLOAD TO YOUTUBE ==========
def upload_to_youtube(video_path, title, description, category_id="22", privacy_status="public"):
    youtube = get_authenticated_service()
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["faceless", "AI generated", "automated"],
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status
        }
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    response = request.execute()
    return response

# ========== MAIN INTERFACE WITH BIG TITLE AND SUBTITLE ==========
col1, col2 = st.columns([4, 1])

with col1:
    st.markdown('<div class="big-title">🎬 Faceless Video Automator with Grok AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Generate and auto-post faceless videos daily using AI.</div>', unsafe_allow_html=True)

with col2:
    st.image(
        "https://raw.githubusercontent.com/Deslandes1/Generate-faceless-videos/main/Gesner%20Deslandes.png",
        width=120,
        caption="Gesner Deslandes"
    )

# Input fields
niche = st.text_input("Enter your video niche (e.g., motivation, history, technology)", value="motivation")
style = st.selectbox("Choose video style", ["Dynamic", "Calm", "Inspirational", "Educational"])
auto_post = st.checkbox("Auto‑post to social media (requires OAuth credentials)")
youtube_title = st.text_input("YouTube Video Title", value=f"Faceless Video - {datetime.now().strftime('%Y%m%d')}")
youtube_description = st.text_area("YouTube Video Description", value="Generated automatically by Grok AI and Pexels clips.")
privacy = st.selectbox("YouTube Privacy Status", ["public", "unlisted", "private"])

if st.button("🚀 Generate & Upload to YouTube", use_container_width=True):
    if not GROK_API_KEY:
        st.error("Grok API key not found in Streamlit secrets.")
    elif not YOUTUBE_CLIENT_ID or not YOUTUBE_CLIENT_SECRET:
        st.error("YouTube OAuth credentials missing. Add YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET to secrets.")
    else:
        with st.spinner("Generating script using Grok AI..."):
            # 1. Generate script using Grok API
            headers = {
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json"
            }
            prompt = f"Write a short, engaging script for a faceless video in the {niche} niche. Style: {style}. Keep it under 200 words."
            payload = {
                "model": "grok-1",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 300
            }
            try:
                response = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                script = response.json()["choices"][0]["message"]["content"]
                st.success("Script generated successfully.")
                st.text_area("Generated Script", script, height=150)
            except Exception as e:
                st.error(f"Grok API error: {e}")
                st.stop()

        # 2. Generate voiceover (edge-tts)
        with st.spinner("Generating voiceover..."):
            voice = "en-US-JennyNeural"
            output_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            async def tts():
                comm = edge_tts.Communicate(script, voice)
                await comm.save(output_audio)
            asyncio.run(tts())
            st.success("Voiceover generated.")

        # 3. Fetch stock clips from Pexels (if API key provided)
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
                        data = resp.json()
                        for video in data.get("videos", []):
                            video_files = video.get("video_files", [])
                            if video_files:
                                clip_url = video_files[0]["link"]
                                clip_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                                clip_resp = requests.get(clip_url, stream=True)
                                with open(clip_path, "wb") as f:
                                    for chunk in clip_resp.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                video_clips.append(clip_path)
                    else:
                        st.warning("Pexels API limit or error. Using fallback black screen.")
                except:
                    st.warning("Could not fetch stock clips. Using fallback.")
            if not video_clips:
                video_clips = [None]
        else:
            video_clips = [None]

        # 4. Assemble video with moviepy
        with st.spinner("Assembling final video..."):
            audio_clip = AudioFileClip(output_audio)
            duration = audio_clip.duration
            clips = []
            for i, clip_path in enumerate(video_clips):
                if clip_path is None:
                    txt_clip = TextClip(script[:100], fontsize=24, color='white', font='Arial', size=(640,480))
                    txt_clip = txt_clip.set_duration(duration/len(video_clips) if len(video_clips)>0 else duration).set_position('center')
                    bg_clip = ColorClip(size=(640,480), color=(0,0,0), duration=duration/len(video_clips) if len(video_clips)>0 else duration)
                    clip = CompositeVideoClip([bg_clip, txt_clip])
                else:
                    clip = VideoFileClip(clip_path).subclip(0, duration/len(video_clips))
                    clip = clip.resize((640,480))
                clips.append(clip)
            final_video = concatenate_videoclips(clips, method="compose")
            final_video = final_video.set_audio(audio_clip)
            output_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
            final_video.write_videofile(output_video, fps=24, codec='libx264', audio_codec='aac')
            st.success("Video assembled successfully!")
            st.video(output_video)

        # 5. Upload to YouTube
        if auto_post:
            with st.spinner("Uploading to YouTube..."):
                try:
                    upload_result = upload_to_youtube(
                        video_path=output_video,
                        title=youtube_title,
                        description=youtube_description,
                        privacy_status=privacy
                    )
                    video_id = upload_result['id']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    st.success(f"Video uploaded successfully! [Watch on YouTube]({video_url})")
                except Exception as e:
                    st.error(f"YouTube upload failed: {e}")
        else:
            st.info("Auto‑posting disabled. You can download the video manually.")

        # 6. Download button (always available)
        with open(output_video, "rb") as f:
            st.download_button("📥 Download Video", f, file_name=f"faceless_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
