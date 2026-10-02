file_path = r"d:\massdrips-voice-agent\backend\routes\smart.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("\ufeff", "")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Removed internal BOMs")
