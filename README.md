# thai-reel-skills: ชุดสกิลตัดต่อ Reel ภาษาไทยสำหรับ Claude Code

ใช้แปลงคลิปคนพูดภาษาไทยเป็น Reel/TikTok แนวตั้ง 9:16 ยาวไม่เกิน 60 วินาที ทำออกมาในสไตล์ที่อนุมัติไว้แล้ว:

- แบ่งจอ split screen โดยให้ภาพประกอบจาก Pexels, แอนิเมชัน 2D/3D หรือการ์ดสินค้า Amway อยู่ด้านบน 58% และคนพูดอยู่ด้านล่าง
- ซับเป็นตัวเหลืองและไฮไลต์ทีละคำ
- ตัดคำว่า ค่ะ/นะคะ/ครับ ออก
- ปรับความดังเสียงเป็น -14 LUFS
- ทำหน้าปกให้ทุกคลิป

## ติดตั้ง

```bash
git clone https://github.com/Chayootpong1/thai-reel-skills.git ~/thai-reel-skills && ~/thai-reel-skills/install.sh
```

สคริปต์ติดตั้งจะทำสิ่งต่อไปนี้:

1. ก๊อปสกิล 15 ตัวไปไว้ที่ `~/.claude/skills/` ถ้ามีสกิลชื่อเดียวกันอยู่แล้ว จะสำรองตัวเดิมเป็น `.bak-*` ก่อน
2. ก๊อปโปรเจกต์ Remotion `split-broll/` และ `product-cartoons/` ไปไว้ที่ `~/ReelStudio/` ถ้าต้องการที่อื่น ให้รันด้วย `REEL_HOME=/path`
3. แก้ path ในสกิลให้ชี้ไปที่ `REEL_HOME`
4. รัน `npm install` และดาวน์โหลดเสียงประกอบ 246 MB จาก Google Drive

อัปเดตเป็นเวอร์ชันใหม่ด้วย `cd ~/thai-reel-skills && git pull && ./install.sh`

## สิ่งที่ต้องมีในเครื่อง

| เครื่องมือ | วิธีติดตั้ง |
|---|---|
| Claude Code | https://claude.com/claude-code |
| Node.js 20 ขึ้นไป | https://nodejs.org |
| ffmpeg (ต้องมี libass) | `brew install ffmpeg` |
| Python venv สำหรับถอดเสียง | `python3 -m venv ~/.venvs/whisper && ~/.venvs/whisper/bin/pip install faster-whisper torch torchaudio transformers pythainlp numpy` |
| plugin HyperFrames | ใน Claude Code: `/plugin marketplace add heygen-com/hyperframes` แล้ว `/plugin install hyperframes@hyperframes` |
| plugin Remotion | `/plugin marketplace add remotion-dev/claude-code-plugin` แล้ว `/plugin install remotion@remotion` |

โมเดลถอดเสียงขนาดประมาณ 4 GB จะดาวน์โหลดเองในการใช้งานครั้งแรก และเก็บไว้ที่ `~/ReelStudio/tools-cache/huggingface`

## วิธีใช้

เปิด Claude Code ในโฟลเดอร์ `~/ReelStudio` ลากไฟล์คลิปเข้ามา แล้วพิมพ์ **"เริ่มทำงาน"**

ระบบจะใช้สกิล `thai-talking-head-edit` เป็นตัวหลัก และเรียกสกิลอื่นต่อกันตามลำดับนี้:

transcript → reel-hook → reel-rough-cut → captions-th → broll-selector → visual-insert / 3d-motion-director → sound-design → reel-motion → reel-export-qc

ระหว่างทำ ระบบจะให้คุณเลือกหน้าปกจากภาพที่ใส่หมายเลขไว้

## ในชุดนี้มีอะไร

- `skills/`: สกิล 15 ตัว
- `split-broll/`: โปรเจกต์ Remotion ที่ใช้ประกอบคลิป ดู README ในโฟลเดอร์สำหรับรูปแบบของ Master Edit Plan ส่วน `src/data/` มีแผนตัดต่อตัวอย่าง 1 คลิป (ไม่มีไฟล์วิดีโอ)
- `product-cartoons/`: `catalog.json` รวมสินค้า Amway TH 278 รายการ และคลิปการ์ตูนสินค้าแบบพื้นหลังโปร่งใส 158 คลิปใน `webm/`

ไม่ได้ใส่ไว้ในชุด: วิดีโอ รูป และไฟล์ render ของคลิปจริง รูป png ของการ์ตูนสินค้า และโมเดล AI
