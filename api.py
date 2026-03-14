import requests

API_KEY = "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"

url = "https://api.groq.com/openai/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "openai/gpt-oss-120b",
    "messages": [
        {"role": "user", "content": "Привіт! Розкажи короткий жарт"}
    ]
}

response = requests.post(url, headers=headers, json=data)

print(response.json())