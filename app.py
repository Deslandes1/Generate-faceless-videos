import streamlit as st
import requests
import tempfile
import asyncio
import edge_tts
from moviepy.editor import *
from datetime import datetime

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
    .main-title {
        text-align: center;
        margin-bottom: 1rem;
        position: relative;
    }
    .main-title h1 {
        color: #1e3c72;
    }
    .main-title p {
        color: #2a4a7a;
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
        word-break: break-all;
    }
    .chat-message {
        background: rgba(255,255,255,0.7);
        border-radius: 15px;
        padding: 10px;
        margin: 5px 0;
        color: #1a2a3a;
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
YOUTUBE_API_KEY = get_secret("YOUTUBE_API_KEY", "")
TIKTOK_ACCESS_TOKEN = get_secret("TIKTOK_ACCESS_TOKEN", "")
INSTAGRAM_TOKEN = get_secret("INSTAGRAM_TOKEN", "")

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

# ========== MAIN INTERFACE WITH PROFILE PICTURE ON THE RIGHT ==========
col1, col2 = st.columns([4, 1])

with col1:
    st.markdown("🎬 **Faceless Video Automator with Grok AI**")
    st.markdown("Generate and auto-post faceless videos daily using AI.")

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

if st.button("🚀 Generate & Post Video", use_container_width=True):
    if not GROK_API_KEY:
        st.error("Grok API key not found in Streamlit secrets. Please add GROK_API_KEY.")
    else:
        with st.spinner("Generating script using Grok AI..."):
            # 1. Generate script using Grok API
            headers = {
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json"
            }
            prompt = f"Write a short, engaging script for a faceless video in the {niche} niche. Style: {style}. Keep it under 200 words."
            payload = {
                "model": "grok-1",  # Adjust if Grok uses a different model name
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

        # 5. Auto-post to social media (requires OAuth – placeholder)
        if auto_post:
            posted = False
            if YOUTUBE_API_KEY:
                st.info("YouTube auto-upload requires OAuth 2.0 credentials (Client ID & Secret). Set up OAuth in your app.")
            if TIKTOK_ACCESS_TOKEN:
                st.info("TikTok upload requires additional OAuth setup. Not implemented in this demo.")
            if INSTAGRAM_TOKEN:
                st.info("Instagram upload requires Graph API setup. Not implemented in this demo.")
            if not posted:
                st.warning("Auto‑posting not fully implemented. You can download the video manually.")
        else:
            st.info("Auto‑posting disabled. You can download the video manually.")

        # 6. Download button
        with open(output_video, "rb") as f:
            st.download_button("📥 Download Video", f, file_name=f"faceless_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
