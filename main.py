def generate_content_with_gemini(traffic_data):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
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
    print("Gemini Full Response:", json.dumps(res, indent=2)) # Yeh error print karega agar koi hua
    
    if "candidates" not in res:
        raise Exception(f"Gemini API Error: {res}")
        
    text_resp = res["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text_resp)
