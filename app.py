import streamlit as st
import requests
import os
import json
import tempfile
import edge_tts
import asyncio
from moviepy.editor import *
import time
from datetime import datetime

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="Faceless Video Automator | Grok AI",
    page_icon="🎬",
    layout="wide"
)

# ========== SIDEBAR FOR API KEYS ==========
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/null/youtube-play.png", width=80)
    st.markdown("## **Faceless Video Automator**")
    st.markdown("Powered by **Grok AI (xAI)**")
    st.markdown("---")
    
    grok_api_key = st.text_input("Grok API Key (xAI)", type="password")
    pexels_api_key = st.text_input("Pexels API Key (optional for stock clips)", type="password")
    
    st.markdown("---")
    st.markdown("**Social Media APIs (optional)**")
    youtube_api_key = st.text_input("YouTube API Key", type="password")
    tiktok_access_token = st.text_input("TikTok Access Token", type="password")
    instagram_token = st.text_input("Instagram Graph API Token", type="password")
    
    st.markdown("---")
    st.markdown("Built by **Gesner Deslandes**")
    st.markdown("📞 (509) 4738 5663")
    st.markdown("✉️ deslandes78@gmail.com")
    st.markdown("🌐 [GlobalInternet.py](https://globalinternetsitepy-abh7v6tnmskxxnuplrdcgk.streamlit.app/)")

# ========== MAIN INTERFACE ==========
st.title("🎬 Faceless Video Automator with Grok AI")
st.markdown("Generate and auto-post faceless videos daily using AI.")

niche = st.text_input("Enter your video niche (e.g., motivation, history, technology)", value="motivation")
style = st.selectbox("Choose video style", ["Dynamic", "Calm", "Inspirational", "Educational"])
auto_post = st.checkbox("Auto‑post to social media (requires API keys)")

if st.button("🚀 Generate & Post Video", use_container_width=True):
    if not grok_api_key:
        st.error("Please enter your Grok API key in the sidebar.")
    else:
        with st.spinner("Generating script using Grok AI..."):
            # 1. Generate script using Grok API
            headers = {
                "Authorization": f"Bearer {grok_api_key}",
                "Content-Type": "application/json"
            }
            prompt = f"Write a short, engaging script for a faceless video in the {niche} niche. Style: {style}. Keep it under 200 words."
            payload = {
                "model": "grok-1",  # adjust if Grok has specific model name
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
        if pexels_api_key:
            with st.spinner("Fetching stock clips from Pexels..."):
                headers_pex = {"Authorization": pexels_api_key}
                # Extract keywords from script (simple: first few words)
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
                                # Download clip
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
                video_clips = [None]  # fallback
        else:
            video_clips = [None]
        
        # 4. Assemble video with moviepy
        with st.spinner("Assembling final video..."):
            audio_clip = AudioFileClip(output_audio)
            duration = audio_clip.duration
            # Create a clip list
            clips = []
            for i, clip_path in enumerate(video_clips):
                if clip_path is None:
                    # Fallback: black screen with text
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
        
        # 5. Auto-post to social media (if requested and keys provided)
        if auto_post:
            posted = False
            if youtube_api_key:
                # YouTube upload would require OAuth, not just API key – simplified for hackathon
                st.info("YouTube auto-upload would require OAuth credentials. Implement separately.")
            if tiktok_access_token:
                st.info("TikTok upload would require API integration. Implement separately.")
            if instagram_token:
                st.info("Instagram Graph API upload requires further setup.")
            if not posted:
                st.warning("Auto‑posting not fully implemented in this demo. Please add OAuth credentials.")
        else:
            st.info("Auto‑posting disabled. You can download the video manually.")
        
        # 6. Download button
        with open(output_video, "rb") as f:
            st.download_button("📥 Download Video", f, file_name=f"faceless_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
