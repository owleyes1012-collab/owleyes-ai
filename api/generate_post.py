# api/generate_post.py
from flask import Flask, request, jsonify
import os, requests, openai

app = Flask(__name__)

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
ZAP_URL = os.environ.get("ZAP_WEBHOOK_URL")

openai.api_key = OPENAI_KEY

def make_prompt(title, keyword):
    return f"""
You are an SEO copywriter and content marketer for a premium footwear brand called Owleyes.
Produce JSON exactly like this:
{{"meta_title": "...", "meta_description": "...", "slug": "...", "content_html": "..."}}

Requirements:
- Title: {title}
- Target keyword: {keyword}
- Wordcount: ~900 words
- Tone: romantic, premium, slightly seductive
- Include 3 short product recommendation bullets that mention Owleyes subtly
- End with a 2-line CTA encouraging email signup
Return only valid JSON.
"""

@app.route("/api/generate_post", methods=["POST"])
def generate_post():
    data = request.json or {}
    title = data.get("title", "How to Choose Boots for Long Walks")
    keyword = data.get("keyword", "best boots for walking long distance")

    prompt = make_prompt(title, keyword)
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini", # replace if needed
            messages=[{"role":"system","content":"You are a helpful SEO writer."},
                      {"role":"user","content":prompt}],
            max_tokens=2000,
            temperature=0.7
        )
        text = resp['choices'][0]['message']['content'].strip()
        # try to parse JSON inside response
        import json
        content_json = json.loads(text)
    except Exception as e:
        return jsonify({"error":"LLM error","details":str(e)}), 500

    # POST to Zapier for onward routing to Wix
    if ZAP_URL:
        try:
            r = requests.post(ZAP_URL, json=content_json, timeout=15)
            zap_status = r.status_code
        except Exception as e:
            zap_status = f"error:{str(e)}"
    else:
        zap_status = "no_zap_url"

    return jsonify({"status":"ok","zap_status":zap_status,"content":content_json}), 200

if __name__ == "__main__":
    app.run()
