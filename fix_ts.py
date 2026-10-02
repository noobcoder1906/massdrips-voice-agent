file_path = r"d:\massdrips-voice-agent\voxsales-app\src\components\LiveCallModal.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_props = """interface LiveCallModalProps {
  onClose: () => void;
  leadName?: string;
  brandName?: string;
}"""

new_props = """interface LiveCallModalProps {
  isOpen?: boolean;
  onClose: () => void;
  onCallCompleted?: () => void;
  leadName?: string;
  leadPhone?: string;
  brandName?: string;
}"""

content = content.replace(old_props, new_props)
content = content.replace("export default function LiveCallModal({ onClose, leadName = 'Customer', brandName = 'MASS DRIPS' }: LiveCallModalProps) {", 
    "export default function LiveCallModal({ isOpen, onClose, onCallCompleted, leadName = 'Customer', leadPhone, brandName = 'MASS DRIPS' }: LiveCallModalProps) {\n  if (!isOpen) return null;")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed TS props")
