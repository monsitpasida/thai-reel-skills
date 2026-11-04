#!/usr/bin/env bash
# ติดตั้งชุดสกิลตัดต่อ Reel ภาษาไทยสำหรับ Claude Code
# ใช้: ./install.sh            (ติดตั้งงานไว้ที่ ~/ReelStudio)
#      REEL_HOME=/path ./install.sh
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
REEL_HOME="${REEL_HOME:-$HOME/ReelStudio}"
SKILLS="$HOME/.claude/skills"
ORIG="/Volumes/JamesM.2/Claude/Video"

echo "== สกิล → $SKILLS"
BACKUP="$HOME/.claude/skills-backup/$(date +%Y%m%d%H%M%S)"
mkdir -p "$SKILLS" "$REEL_HOME"
for d in "$SRC"/skills/*/; do
  name="$(basename "$d")"
  if [ -d "$SKILLS/$name" ]; then
    # สำรองไว้นอกโฟลเดอร์ skills ไม่งั้น Claude Code จะเห็นเป็นสกิลซ้ำ
    mkdir -p "$BACKUP" && mv "$SKILLS/$name" "$BACKUP/$name"
    echo "   สำรองของเดิม: $BACKUP/$name"
  fi
  cp -R "$d" "$SKILLS/$name"
done

echo "== โปรเจกต์ → $REEL_HOME"
# rsync ไม่ทับ public/ และ src/data ที่เพื่อนสร้างเพิ่มเอง
rsync -a "$SRC/split-broll/" "$REEL_HOME/split-broll/"
rsync -a "$SRC/product-cartoons/" "$REEL_HOME/product-cartoons/"

# เปลี่ยน path ของเครื่องต้นฉบับเป็น path บนเครื่องนี้
files=$(grep -rlF "/Volumes/JamesM.2/Claude" "$SKILLS"/{thai-talking-head-edit,sound-design} "$REEL_HOME/product-cartoons/catalog.json" || true)
for f in $files; do
  sed -i.tmp -e "s#$ORIG#$REEL_HOME#g" -e "s#/Volumes/JamesM.2/Claude/tools-cache#$REEL_HOME/tools-cache#g" "$f" && rm -f "$f.tmp"
done
left=$(grep -rlF "/Volumes/JamesM.2" "$SKILLS"/{thai-talking-head-edit,sound-design} "$REEL_HOME/product-cartoons/catalog.json" || true)
[ -z "$left" ] || { echo "!! ยังมี path เดิมค้างใน: $left"; exit 1; }

echo "== ตรวจเครื่องมือ"
miss=0
for t in node npm ffmpeg python3; do
  if command -v "$t" >/dev/null 2>&1 || [ "$t" = ffmpeg -a -x "$HOME/.local/bin/ffmpeg" ]; then echo "   ✓ $t"; else echo "   ✗ $t (ต้องติดตั้งเพิ่ม)"; miss=1; fi
done
if command -v npm >/dev/null 2>&1; then
  (cd "$REEL_HOME/split-broll" && npm install --no-audit --no-fund >/dev/null) && echo "   ✓ npm install split-broll"
fi
if [ -x "$HOME/.venvs/whisper/bin/python" ]; then echo "   ✓ venv ~/.venvs/whisper"; else
  echo "   ✗ venv ถอดเสียง ยังไม่มี สร้างด้วย:"
  echo "     python3 -m venv ~/.venvs/whisper && ~/.venvs/whisper/bin/pip install faster-whisper torch torchaudio transformers pythainlp numpy"
  miss=1
fi

echo "== เสียงประกอบ (246 MB จาก Google Drive)"
bash "$SKILLS/sound-design/scripts/install-sfx.sh" || echo "   ✗ ดาวน์โหลดไม่สำเร็จ รันซ้ำทีหลัง: bash ~/.claude/skills/sound-design/scripts/install-sfx.sh"

echo
echo "เสร็จแล้ว งานอยู่ที่ $REEL_HOME"
echo "ติดตั้ง plugin เพิ่มใน Claude Code: hyperframes, remotion (ดู README)"
[ $miss = 0 ] || echo "มีเครื่องมือที่ยังขาด ดูรายการ ✗ ด้านบน"
echo "เปิด Claude Code ในโฟลเดอร์ $REEL_HOME แล้วลากคลิปเข้ามาพิมพ์ \"เริ่มทำงาน\""
