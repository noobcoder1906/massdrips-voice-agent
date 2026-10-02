file_path = r"d:\massdrips-voice-agent\backend\routes\smart.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

if "from backend.agent.rag_engine import rag" not in content:
    content = "from backend.agent.rag_engine import rag\n" + content
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("Fixed smart.py import!")
