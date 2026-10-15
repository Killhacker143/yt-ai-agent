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

CLIENT_ID = os.environ["YOUTUBE_CLIENT_ID"]
CLIENT_SECRET = os.environ["YOUTUBE_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["YOUTUBE_REFRESH_TOKEN"]

def get_youtube_client():
    creds = Credentials(
        None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
    return build("youtube", "v3", credentials=creds)

def get_fallback_content():
    return {
        "title": "Duniya ke sabse amazing tech secrets #shorts #viral",
        "description": "Kya aapko pata hai yeh gazab tech fact? Video dekhein aur channel ko subscribe karein! #shorts #viral #tech #facts",
        "tags": ["shorts", "viral", "facts", "tech", "hindi"],
        "voice_script": "Kya aapko pata hai ki duniya ki sabse tezi se badalne wali technology aane wale samay mein hamari zindagi puri tarah badal degi? Aise hi rochak aur hairan karne wale facts ke liye abhi channel ko subscribe karein!",
        "image_prompts": [
            "Futuristic glowing technology background vertical 9:16",
            "Advanced artificial intelligence brain concept 9:16",
            "Cyber security matrix background vertical 9:16",
            "Hitech digital world map glowing 9:16"
        ]
    }

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
    print("1. Preparing Content & Script...")
    data = get_fallback_content()
    print("Selected Title:", data["title"])
    
    print("2. Generating Free Voiceover...")
    asyncio.run(create_voiceover(data["voice_script"], "voice.mp3"))
    
    print("3. Generating Free AI Visuals...")
    images = download_ai_images(data["image_prompts"])
    
    print("4. Rendering Video...")
    build_video(images, "voice.mp3", "final_short.mp4")
    
    print("5. Connecting to YouTube...")
    yt = get_youtube_client()
    
    print("6. Uploading to YouTube...")
    upload_to_youtube(yt, "final_short.mp4", data)
