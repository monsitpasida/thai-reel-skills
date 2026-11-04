# split-broll — Dynamic Contextual B-roll Split Screen

Remotion 4 · 1080×1920 · 30 fps

ในสภาพปกติคนพูดเต็มจอ เมื่อถึงช่วงที่มีภาพประกอบ คนพูดจะเลื่อนลงไปอยู่ล่าง 42% และ B-roll เปิดลงมาจากด้านบน 58% รอยต่อเป็นแถบ feather + blur ไม่มีเส้นแบ่ง ซับย้ายไปอยู่บนรอยต่อ (ใต้ subject ของ B-roll และเหนือหน้าคนพูด) แล้วกลับลงไปเมื่อ insert จบ

## ไฟล์

| ไฟล์ | หน้าที่ |
|---|---|
| `src/split/ContextualSplitInsert.tsx` | component หลัก ใช้ซ้ำได้ |
| `src/split/geometry.ts` | `coverRect()` (cover + เล็ง subject, ไม่ยืดภาพ) และ `splitProgress()` (เส้นเวลา transition ที่ insert กับซับใช้ร่วมกัน) |
| `src/split/plan.ts` | แปลง Master Edit Plan (วินาที) เป็นเฟรม พร้อมกฎ whoosh, ความยาว และลูกเล่นที่สลับกันไปในแต่ละ insert |
| `src/split/SplitCaptions.tsx` | ซับไฮไลต์ทีละคำตามสไตล์ที่อนุมัติ อิง timestamp ระดับคำเดิม |
| `src/SplitReel.tsx` | composition: คนพูดเต็มจอ (เสียงพูดเล่นต่อเนื่องจากที่นี่ที่เดียว) + inserts + ซับ |
| `src/data/edit-plan.json` | Master Edit Plan = source of truth |
| `src/data/captions.json` | ซับระดับคำ (รูปแบบเดียวกับ `.video-edit/captions.json`) |

## Master Edit Plan

```json
{
  "whoosh": "demo/whoosh.wav",
  "inserts": [
    {
      "type": "contextual-split-insert",
      "start": 11.0,
      "end": 15.0,
      "visual": "demo/broll.mp4",
      "layout": "top-broll-bottom-speaker",
      "topRatio": 0.58,
      "bottomRatio": 0.42,
      "seamStyle": "soft-blur-feather",

      "visualStart": 6.7,
      "focus": { "x": 0.5, "y": 0.34 },
      "reason": "explain",
      "spokenContext": "…",
      "sfx": "auto",
      "visualAudio": false,
      "captionY": 1118
    }
  ]
}
```

- `start` / `end` เป็นวินาทีบน timeline ของคลิปหลัก รวมช่วง transition เข้าและออกแล้ว
- `visual` คือ path ใน `public/` หรือ URL จะเป็นวิดีโอ หรือรูปนิ่ง (.jpg/.png/.webp) ก็ได้ รูปนิ่งจะขยับเองด้วย Ken Burns ส่วน `visualStart` คือวินาทีในไฟล์วิดีโอที่เริ่มเล่น
- `cuts` ใช้ตัดไปภาพอื่นในกรอบบนโดยไม่ออกจาก split เช่น `[{"at": 33.88, "visual": "pexels/grapes.mp4", "visualStart": 2, "focus": {...}}]` โดย `at` เป็นวินาทีบน timeline หลัก เหมาะกับประโยคที่พูดถึงหลายสิ่งติดกัน
- `focus` คือจุดของ subject ในภาพ B-roll (0..1) ที่ต้องการให้อยู่กลางพื้นที่ด้านบน ระบบจะ crop แบบ cover รอบจุดนี้
- `reason` ต้องเป็นค่าใดค่าหนึ่งใน explain / visualize / prove / context / demonstrate / reset-attention ถ้าตอบไม่ได้ว่าช่วยอะไร ไม่ควรใส่ insert นั้น
- `sfx`: `auto` จะใส่ whoosh เบา ๆ เฉพาะ insert แรก หรือ insert ที่ห่างจากอันก่อนหน้า 4 วิขึ้นไป ใช้ `whoosh` เพื่อบังคับใส่ หรือ `none` เพื่อปิด
- `visualAudio: true` จะเปิดเสียง B-roll (`visualVolume` ค่าเริ่มต้น 0.6) ใช้เฉพาะตอนที่เสียงนั้นสำคัญต่อเหตุการณ์ ค่าเริ่มต้นคือปิดเสียง
- ถ้า insert สั้นกว่า 1.5 วิหรือยาวกว่า 4 วิ หรือซ้อนกัน จะขึ้น warning ใน console

## การ์ดสินค้า (`products`)

```json
"pop": "sfx/pop.mp3",
"products": [
  { "start": 16.5, "end": 17.9, "image": "products/nutrilite-vitamin-d3-k2.png", "side": "right",
    "source": "https://amway.co.th/product/nutrilite-vitamin-d3-k2/341899TH" }
]
```

ถ้า `image` เป็นไฟล์ `.webm` (การ์ตูนสินค้าแบบโปร่งใสจาก `product-cartoons/catalog.json` วางไว้ที่ `public/cartoons/`) การ์ดจะเล่นคลิปการ์ตูน 3 วินาทีแทน ไม่มีการ์ดขาว ขนาดใหญ่กว่าการ์ดรูป 1.35 เท่า และเฟดออกตอนท้าย

ใช้รูปสินค้าจริงจาก amway.co.th ที่ครอปขอบขาวออกแล้ว แสดงบนการ์ดสีขาวที่ pop ขึ้นตรงคำที่พูดถึงสินค้าพร้อมเสียง pop ให้วางการ์ดภายในช่วง split เสมอ และใช้ `side` เลือกมุมของพื้นที่ B-roll ที่ไม่ทับ subject

## แอนิเมชัน 2D/3D

`public/anim/bone-explainers-2d-3d.webm` คือไฟล์ที่ render จาก `bone-anim/` (HyperFrames) มีทั้งหมด 6 ฉาก ใช้เป็น `visual` ได้เหมือน B-roll โดยตั้ง `visualStart` เป็นจุดเริ่มของแต่ละฉาก ได้แก่ skin 0, team 6.63, absorb 11.97, calmag 17.97, shield 23.24 และ inside3d (3D) 28.5 จังหวะในแต่ละฉากผูกกับคำพูดของคลิปกระดูกไว้แล้ว จึงต้องตั้ง `start` ให้ตรงกับเวลาในแผนเดิม (สูตร: visualStart = จุดเริ่มฉาก + (start − เวลาใน reel ที่ฉากเริ่ม))

## Transition ที่ไม่ซ้ำแบบ template

แต่ละ insert จะสลับค่าเหล่านี้ไปตามลำดับ โดยทุกค่ายังอยู่ในกรอบที่กำหนด:

- ความยาวช่วงเข้า 0.33 / 0.37 / 0.30 วิ และช่วงออก 0.30 / 0.33 / 0.27 วิ
- easing แบบ ease-out (expo) สลับกับ spring ที่ damping 200 ซึ่งไม่มีการเด้ง
- Ken Burns ของ B-roll วนเป็น push-in → drift-left → pull-out → drift-right

## ใช้ component ตรง ๆ

```tsx
<ContextualSplitInsert
  mainVideo="clip.mp4"
  brollVideo="broll/market.mp4"
  startFrame={330}
  durationInFrames={120}
  topRatio={0.58}
  transitionFrames={10}
  blurAmount={14}
  featherSize={96}
  brollStartTime={2.5}
/>
```

ต้องวางทับบน `<Video>` ของคนพูดแบบเต็มจอ ซึ่งเป็นตัวที่มีเสียง เพราะ insert จะสร้างสำเนาภาพคนพูดแบบปิดเสียงขึ้นมาเองในช่วงนั้น ใส่กี่ insert ก็ได้ แค่ map ไปทีละตัว

## คำสั่ง

```bash
npm run dev                      # Remotion Studio
npx remotion render SplitReel out/reel.mp4
npx remotion render SplitReel out/reel.mp4 --props=path/to/props.json   # คลิปอื่น: mainVideo, editPlan, captions, speakerFocusY
```

`speakerFocusY` คือตำแหน่งแนวตั้งของหน้าคนพูดในเฟรมต้นฉบับ (0..1) ค่าเริ่มต้นคือ 0.45 ใช้ค่านี้คำนวณว่าต้องเลื่อนภาพลงเท่าไรให้หน้าอยู่กลางพื้นที่ด้านล่าง

## ที่มาของภาพ

รูปสินค้าใน `public/products/` มาจาก amway.co.th ตามลิงก์ใน `source` ของแผน

### B-roll (Pexels License, ใช้ฟรี ไม่ต้องให้เครดิต)

| ไฟล์ใน `public/pexels/` | ที่มา |
|---|---|
| skincare-9474154.mp4 | https://www.pexels.com/video/9474154/ |
| sunlight-15365455.mp4 | https://www.pexels.com/video/15365455/ |
| capsules-31555271.jpg | https://www.pexels.com/photo/31555271/ |
| pomegranate-8803789.mp4 | https://www.pexels.com/video/8803789/ |
| grapes-7213754.mp4 | https://www.pexels.com/video/7213754/ |
