file_path = r"d:\massdrips-voice-agent\backend\routes\smart.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Remove the hardcoded fallback
target = """    reply_text = "".join(tokens).strip()
    if not reply_text:
        reply_text = "Haan bilkul! Our tees start at 699 and hoodies at 1499. Which style do you like?"""

replacement = """    reply_text = "".join(tokens).strip()
    if not reply_text:
        reply_text = "I'm sorry, I didn't quite catch that. Could you repeat?"""

content = content.replace(target, replacement)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Removed hardcoded fallback")
