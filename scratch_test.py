import urllib.request, uuid, time

boundary = '----Boundary' + uuid.uuid4().hex
with open('backend/voice/clones/test_speak_endpoint.wav', 'rb') as f:
    audio_data = f.read()

part = (
    '--' + boundary + '\r\n'
    'Content-Disposition: form-data; name="file"; filename="audio.wav"\r\n'
    'Content-Type: audio/wav\r\n\r\n'
).encode('utf-8')

body = part + audio_data + ('\r\n--' + boundary + '--\r\n').encode('utf-8')
req = urllib.request.Request(
    'http://localhost:8000/api/v1/smart/transcribe',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
)

start = time.time()
with urllib.request.urlopen(req) as resp:
    print(f"Transcription finished in {(time.time()-start)*1000:.1f}ms!")
    print("Result:", resp.read().decode('utf-8'))
