import urllib.request, json, time

test_queries = [
    "Hey, so I am looking for the collection hoodies which you have.",
    "What is the cost actually?",
    "Do you have oversized black hoodies in stock?"
]

for q in test_queries:
    data = json.dumps({
        "message": q,
        "voice": "en-IN-PrabhatNeural",
        "lead_name": "Priya"
    }).encode("utf-8")
    req = urllib.request.Request("http://localhost:8000/api/v1/smart/fast-turn", data=data, headers={"Content-Type": "application/json"})
    
    t0 = time.time()
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    t1 = time.time()
    
    print(f'User: "{q}"')
    print(f'-> AI Reply: "{res.get("reply")}"')
    print(f'-> Total Latency: {t1-t0:.3f}s (Server internal: {res.get("duration_ms")}ms) | Audio Bytes: {len(res.get("audio_base64", ""))}\n')
