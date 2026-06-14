import streamlit as st
import requests
import tempfile
import asyncio
from gtts import gTTS
from moviepy.editor import *
from moviepy.audio.AudioClip import AudioClip
from datetime import datetime
import os
import pickle
import numpy as np
from PIL import Image, ImageDraw, ImageFont
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
PEXELS_API_KEY = st.secrets.get("PEXELS_API_KEY", "")
YOUTUBE_CLIENT_ID = st.secrets.get("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = st.secrets.get("YOUTUBE_CLIENT_SECRET", "")
REDIRECT_URI = st.secrets.get("REDIRECT_URI", "https://your-app.streamlit.app")

if not GROQ_API_KEY:
    st.error("GROK_API_KEY (Groq key) is missing. Please add it to Streamlit secrets.")
    st.stop()

# ========== LANGUAGE MAPPING ==========
LANG_CODES = {
    "English": "en",
    "French": "fr",
    "Spanish": "es"
}

# ========== CUSTOM CSS ==========
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
    
    selected_lang = st.selectbox("🌐 Language for script & voice", list(LANG_CODES.keys()), index=0)
    lang_code = LANG_CODES[selected_lang]
    bg_color = st.color_picker("🎨 Background color for text screen", value="#000000")
    
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

def generate_voice_with_gtts(script, output_path, lang_code):
    try:
        tts = gTTS(text=script, lang=lang_code, slow=False)
        tts.save(output_path)
        return True
    except Exception as e:
        st.error(f"gTTS error: {e}")
        return False

def create_text_clip(text, duration, size=(640,480), fontsize=24, bg_color=(0,0,0), decorate=False):
    display_text = text
    if decorate:
        stars_line = "★ ★ ★ ★ ★"
        emoji_line = "😂 😂 😂 😂 😂"
        display_text = stars_line + "\n\n" + text + "\n\n" + emoji_line
    
    img = Image.new('RGB', size, color=bg_color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize)
    except:
        font = ImageFont.load_default()
    words = display_text.split()
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
    if not lines:
        lines = [display_text]
    line_height = fontsize + 6
    total_height = len(lines) * line_height
    y = (size[1] - total_height) // 2
    for line in lines:
        draw.text((10, y), line, fill='white', font=font)
        y += line_height
    img_array = np.array(img)
    clip = ImageClip(img_array, duration=duration)
    return clip

def create_image_clip_with_cursor(image_file, duration, cursor_img, cursor_positions, target_size=(640,480)):
    """
    Create a video clip from an image. If cursor_img is not None and cursor_positions is a dict
    of (time_ratio, (x,y)) for that image, we overlay the cursor at the given positions.
    For simplicity, we will assume the cursor appears at a fixed position for the entire duration
    of each paragraph segment. Since we call this function per image with the total duration,
    we need to segment the clip into subclips with different cursor positions.
    However, to keep it manageable, we'll create a single clip where the cursor appears at a single
    position (the first coordinate) for the whole image? That won't work.
    
    Better: We'll create a composite of the background image and the cursor image placed at the given
    coordinates for the entire duration. But we need different positions for each paragraph.
    
    Actually, we are already splitting the audio per paragraph and creating separate visual clips
    for each image. But for the first image, we want the same background image but with different
    cursor positions for each paragraph. Therefore, we should create three separate clips for the first
    image, each with the cursor at the appropriate coordinates, and then concatenate them.
    
    Let's do this: For the first image, instead of creating one long clip, we will create one clip per
    paragraph of that image, each with the cursor overlay at its assigned coordinates.
    """
    # Load the background image and resize
    bg_img = Image.open(image_file).convert('RGB')
    bg_img = bg_img.resize(target_size, Image.Resampling.LANCZOS)
    bg_np = np.array(bg_img)
    
    if cursor_img is None or cursor_positions is None:
        # No cursor, just return a plain ImageClip
        return ImageClip(bg_np, duration=duration)
    
    # Load cursor image (PNG with transparency)
    cursor_pil = Image.open(cursor_img).convert('RGBA')
    # Resize cursor to a reasonable size (e.g., 40x40)
    cursor_pil = cursor_pil.resize((40, 40), Image.Resampling.LANCZOS)
    cursor_np = np.array(cursor_pil)
    
    # For the entire clip, we need to overlay the cursor at the given (x,y) for the whole duration
    # We'll create a function that returns a frame with the cursor overlaid
    def make_frame(t):
        frame = bg_np.copy()
        # Convert frame to PIL to overlay
        frame_pil = Image.fromarray(frame)
        # Paste cursor at (x, y)
        x, y = cursor_positions
        frame_pil.paste(cursor_pil, (x, y), cursor_pil)  # using mask
        return np.array(frame_pil)
    
    return VideoClip(make_frame, duration=duration)

# ========== SCRIPT SPLITTER WITH MULTI‑PARAGRAPH PER IMAGE ==========
def split_script_for_images(script, num_images, paragraphs_per_image):
    paragraphs = [p.strip() for p in script.split('\n\n') if p.strip()]
    total_needed = sum(paragraphs_per_image)
    if len(paragraphs) != total_needed:
        st.warning(f"Script has {len(paragraphs)} paragraphs but you specified {total_needed} paragraphs total. Using as many as available.")
    image_paragraphs = []
    start = 0
    for i, count in enumerate(paragraphs_per_image):
        end = start + count
        image_paragraphs.append(paragraphs[start:end])
        start = end
    return image_paragraphs

# ========== INIT SESSION STATE ==========
if 'manual_script' not in st.session_state:
    st.session_state.manual_script = ""
if 'use_manual' not in st.session_state:
    st.session_state.use_manual = False

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

niche = st.text_input("Enter your video niche (e.g., motivation, history, technology)", value="science education")
style = st.selectbox("Choose video style", ["Dynamic", "Calm", "Inspirational", "Educational"])
auto_post = st.checkbox("Auto‑post to YouTube (requires OAuth)")
youtube_title = st.text_input("YouTube Video Title", value=f"Educational Video - {datetime.now().strftime('%Y%m%d')}")
youtube_description = st.text_area("YouTube Video Description", value="Generated automatically by Groq AI and gTTS voice.")
privacy = st.selectbox("YouTube Privacy Status", ["public", "unlisted", "private"])

st.markdown("---")
st.subheader("📸 Use Your Own Images (Slideshow)")
uploaded_images = st.file_uploader(
    "Upload images (PNG, JPG) – they will be displayed in order",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)
use_images = uploaded_images and len(uploaded_images) > 0
if use_images:
    num_images = len(uploaded_images)
    st.success(f"{num_images} images uploaded.")
    st.write("How many script paragraphs should each image display?")
    paragraphs_per_image = []
    for i in range(num_images):
        ppi = st.number_input(f"Paragraphs for Image {i+1}", min_value=1, value=3 if i==0 else 1, step=1, key=f"ppi_{i}")
        paragraphs_per_image.append(ppi)
    st.info(f"Total paragraphs needed: {sum(paragraphs_per_image)}. Write your script with exactly that many paragraphs (separated by blank lines).")
    
    # Cursor pointer for the first image
    if num_images >= 1:
        st.markdown("---")
        st.subheader("🖱️ Cursor Pointer for First Image")
        cursor_file = st.file_uploader("Upload a cursor image (PNG with transparency)", type=["png"], key="cursor_upload")
        if cursor_file:
            cursor_image = cursor_file
            st.success("Cursor image uploaded. Now specify coordinates for each paragraph of the first image.")
            st.info("Coordinates are in pixels on a 640x480 canvas. The top‑left is (0,0).")
            cursor_coords = []
            total_para_first = paragraphs_per_image[0]
            for p in range(total_para_first):
                col1, col2 = st.columns(2)
                with col1:
                    x = st.number_input(f"Paragraph {p+1} - X coordinate", value=320, key=f"x_{p}")
                with col2:
                    y = st.number_input(f"Paragraph {p+1} - Y coordinate", value=240, key=f"y_{p}")
                cursor_coords.append((x, y))
        else:
            cursor_image = None
            cursor_coords = []
    else:
        cursor_image = None
        cursor_coords = []
else:
    st.info("No images uploaded. Will use stock video clips from Pexels (or text fallback).")

st.markdown("---")
st.subheader("📝 Script Source")
use_manual_script = st.checkbox("✍️ Use my own script instead of AI‑generated", value=st.session_state.use_manual)
st.session_state.use_manual = use_manual_script

if use_manual_script:
    manual_script_text = st.text_area("Paste your custom script below (paragraphs separated by blank lines):", value=st.session_state.manual_script, height=400)
    if st.button("Save Custom Script"):
        if manual_script_text.strip():
            st.session_state.manual_script = manual_script_text.strip()
            st.success("Custom script saved!")
        else:
            st.error("Please enter a non‑empty script.")
    st.info(f"Current custom script length: {len(st.session_state.manual_script)} characters.")
else:
    pass

if st.button("🚀 Generate & Upload to YouTube", use_container_width=True):
    if not GROQ_API_KEY:
        st.error("Groq API key missing in secrets.")
    elif auto_post and (not YOUTUBE_CLIENT_ID or not YOUTUBE_CLIENT_SECRET):
        st.error("YouTube OAuth credentials missing.")
    else:
        # ---------- 1. Get script ----------
        if use_manual_script:
            if not st.session_state.manual_script:
                st.error("You selected manual script but no script saved. Please paste your script and click 'Save Custom Script' first.")
                st.stop()
            script = st.session_state.manual_script
            st.success("Using your custom script.")
            st.text_area("Your Script", script, height=150)
        else:
            with st.spinner(f"Generating script using Groq AI (Llama 3.1) in {selected_lang}..."):
                api_url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                lang_instruction = f"Write the script in {selected_lang}."
                prompt = f"Write a short, engaging script for a faceless video in the {niche} niche. Style: {style}. Keep it under 200 words. {lang_instruction}"
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
                    st.success(f"Script generated in {selected_lang}!")
                    st.text_area("Generated Script", script, height=150)
                except Exception as e:
                    st.error(f"Groq API error: {e}")
                    st.stop()

        # ---------- 2. Prepare visual and audio segments for images ----------
        if use_images:
            # Split script according to user-defined paragraphs per image
            paragraphs = [p.strip() for p in script.split('\n\n') if p.strip()]
            total_needed = sum(paragraphs_per_image)
            if len(paragraphs) != total_needed:
                st.error(f"Script has {len(paragraphs)} paragraphs but you specified {total_needed} total. Please adjust the number of paragraphs per image or your script.")
                st.stop()
            image_paragraphs = []
            start = 0
            for count in paragraphs_per_image:
                image_paragraphs.append(paragraphs[start:start+count])
                start += count
            
            # Generate audio for each paragraph of each image
            audio_segments = []  # list of audio file paths per paragraph (in order)
            temp_files = []
            for img_idx, para_list in enumerate(image_paragraphs):
                for para in para_list:
                    if not para.strip():
                        para = f"Image {img_idx+1} content"
                    audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
                    if generate_voice_with_gtts(para, audio_path, lang_code):
                        audio_segments.append(audio_path)
                        temp_files.append(audio_path)
                    else:
                        st.error(f"Voice generation failed for paragraph of image {img_idx+1}.")
                        st.stop()
            
            # Concatenate all audio segments into one file
            with st.spinner("Concatenating audio segments..."):
                final_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
                clips = [AudioFileClip(p) for p in audio_segments]
                combined = concatenate_audioclips(clips)
                combined.write_audiofile(final_audio, codec='libmp3lame')
                for clip in clips:
                    clip.close()
                output_audio = final_audio
            
            # Create video clips: each image gets multiple clips (one per paragraph)
            visual_clips = []
            audio_idx = 0
            for img_idx, (img_file, para_list) in enumerate(zip(uploaded_images, image_paragraphs)):
                # For the first image, we may have cursor coordinates for each paragraph
                if img_idx == 0 and cursor_image and cursor_coords and len(cursor_coords) == len(para_list):
                    use_cursor = True
                else:
                    use_cursor = False
                for para_idx, para in enumerate(para_list):
                    duration = AudioFileClip(audio_segments[audio_idx]).duration
                    audio_idx += 1
                    if use_cursor:
                        coord = cursor_coords[para_idx]
                        clip = create_image_clip_with_cursor(img_file, duration, cursor_image, coord, target_size=(640,480))
                    else:
                        # No cursor (either second image or no cursor uploaded)
                        clip = create_image_clip_with_cursor(img_file, duration, None, None, target_size=(640,480))
                    visual_clips.append(clip)
            
        else:
            # Original fallback (single audio, single visual)
            with st.spinner(f"Generating voiceover in {selected_lang} using gTTS..."):
                output_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
                success = generate_voice_with_gtts(script, output_audio, lang_code)
                if not success:
                    st.error("Voice generation failed. Cannot proceed.")
                    st.stop()
                st.success("Voiceover ready.")
            
            audio_clip = AudioFileClip(output_audio)
            duration = audio_clip.duration
            
            visual_clips = []
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
                                    try:
                                        clip = VideoFileClip(clip_path).subclip(0, duration/3).resize((640,480))
                                        visual_clips.append(clip)
                                    except:
                                        pass
                    except:
                        st.warning("Pexels fetch failed.")
            if not visual_clips:
                bg_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                fontsize = 24 if len(script) <= 400 else 18
                decorated_clip = create_text_clip(script, duration, size=(640,480), fontsize=fontsize, bg_color=bg_rgb, decorate=True)
                visual_clips = [decorated_clip]

        # ---------- 3. Assemble video ----------
        with st.spinner("Assembling video..."):
            if use_images:
                final_video = concatenate_videoclips(visual_clips, method="compose")
                combined_audio = AudioFileClip(output_audio)
                final_video = final_video.set_audio(combined_audio)
            else:
                final_video = concatenate_videoclips(visual_clips, method="compose")
                audio_clip = AudioFileClip(output_audio)
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
