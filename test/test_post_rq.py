import requests

url = "http://localhost:8088/rescue_request/"

payload = {
    "category_id": 1,
    "title": "cuu nguoi voi",
    "content": "help",
    "status": "string",
    "source_id": 2,
    "posted_time": "string",
    "created_date": "2025-12-27T03:33:57.999Z",
    "urgency_score": 0,
    "reliability_score": 0,
    "contract": "string",
    "post_url": "string",
    "region_id": 5,
    "longitude": 0,
    "latitude": 0,
    "location": "string",
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.status_code)
print(response.json())
