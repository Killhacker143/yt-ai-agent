import os
import json
import asyncio
import requests
import urllib.parse
import edge_tts
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Environment Secrets
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
CLIENT_ID = os.environ["YOUTUBE_CLIENT_ID"]
CLIENT_SECRET = os.environ["YOUTUBE_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["YOUTUBE_REFRESH_TOKEN"]

DEFAULT_NICHE = "Amazing Tech, AI Secrets, and Mind-Blowing Facts in Hindi"

def get_youtube_client():
    creds = Credentials(
        None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    return build("youtube", "v3", credentials=creds)

def get_best_performing_topic(youtube):
    try:
        ch_res = youtube.channels().list(part="contentDetails", mine=True).execute()
        uploads_id = ch_res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        
        pl_res = youtube.playlistItems().list(playlistId=uploads_id, part="contentDetails", maxResults=15).execute()
        video_ids = [item["contentDetails"]["videoId"] for item in pl_res.get("items", [])]
        
        if not video_ids:
            return f"No previous videos. Create a viral video on: {DEFAULT_NICHE}"
            
        vid_res = youtube.videos().list(part="snippet,statistics", id=",".join(video_ids)).execute()
        
        performance_summary = []
        for v in vid_res.get("items", []):
            title = v["snippet"]["title"]
            views = int(v["statistics"].get("viewCount", 0))
            likes = int(v["statistics"].get("likeCount", 0))
            performance_summary.append((views, likes, title))
            
        performance_summary.sort(reverse=True)
        top_videos = "\n".join([f"- '{t}' (Views: {v}, Likes: {l})" for v, l, t in performance_summary[:5]])
        return f"Top performing videos on my channel:\n{top_videos}"
    except Exception as e:
        print("Traffic check fallback:", e)
        return f"Create a high-retention viral video on: {DEFAULT_NICHE}"

def generate_content_with_gemini(traffic_data):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    prompt = f"""
    You are an expert YouTube Shorts Growth AI Agent.
    Here is my channel's current traffic data:
    {traffic_data}

    Based on what is getting the most views, generate a new 45-second YouTube Short in engaging Hinglish/Hindi.
    Include a strong 3-second hook at the start and a call-to-action at the end asking viewers to Subscribe.

    Respond ONLY in valid raw JSON format with this exact structure:
    {{
      "title": "Viral catchy title under 60 chars #shorts",
      "description": "SEO description with keywords and hashtags #shorts #viral #facts",
      "tags": ["shorts", "viral", "facts", "tech", "hindi"],
      "voice_script": "Full spoken script in Hindi without any stage directions or emojis.",
      "image_prompts": [
        "Detailed cinematic vertical 9:16 wallpaper prompt for scene 1",
        "Detailed cinematic vertical 9:16 wallpaper prompt for scene 2",
        "Detailed cinematic vertical 9:16 wallpaper prompt for scene 3",
        "Detailed cinematic vertical 9:16 wallpaper prompt for scene 4"
      ]
    }}
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    res = requests.post(url, json=payload).json()
    text_resp = res["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text_resp)

async def create_voiceover(script_text, output_file="voice.mp3"):
    communicate = edge_tts.Communicate(script_text, "hi-IN-MadhurNeural", rate="+8%")
    await communicate.save(output_file)

def download_ai_images(prompts):
    image_files = []
    for i, p in enumerate(prompts):
        encoded = urllib.parse.quote(f"{p}, vertical 9:16 aspect ratio, ultra realistic, 8k, cinematic lighting")
        img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&seed={i+100}"
        res = requests.get(img_url, timeout=60)
        fname = f"scene_{i}.jpg"
        with open(fname, "wb") as f:
            f.write(res.content)
        image_files.append(fname)
    return image_files

def build_video(image_files, audio_file, output_video="final_short.mp4"):
    audio = AudioFileClip(audio_file)
    duration_per_image = audio.duration / len(image_files)
    
    clips = []
    for img in image_files:
        clip = ImageClip(img).set_duration(duration_per_image).resize((1080, 1920))
        clips.append(clip)
        
    final_clip = concatenate_videoclips(clips, method="compose").set_audio(audio)
    final_clip.write_videofile(output_video, fps=24, codec="libx264", audio_codec="aac")

def upload_to_youtube(youtube, video_file, metadata):
    body = {
        "snippet": {
            "title": metadata["title"][:95],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "categoryId": "28"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True, mimetype="video/mp4")
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = req.execute()
    print(f"Uploaded Successfully! Video ID: {response['id']}")

if __name__ == "__main__":
    print("1. Checking Channel Traffic...")
    yt = get_youtube_client()
    traffic_info = get_best_performing_topic(yt)
    print(traffic_info)
    
    print("2. Generating AI Script & SEO Metadata...")
    data = generate_content_with_gemini(traffic_info)
    print("Selected Title:", data["title"])
    
    print("3. Generating Free Voiceover...")
    asyncio.run(create_voiceover(data["voice_script"], "voice.mp3"))
    
    print("4. Generating Free AI Visuals...")
    images = download_ai_images(data["image_prompts"])
    
    print("5. Rendering Video...")
    build_video(images, "voice.mp3", "final_short.mp4")
    
    print("6. Uploading to YouTube...")
    upload_to_youtube(yt, "final_short.mp4", data)
