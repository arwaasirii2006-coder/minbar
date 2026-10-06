# نشر منبر — Deployment

خدمة واحدة تقدّم الواجهة و REST و WebSocket. لا قاعدة بيانات.

## 1. Render (موصى به)

1. ادفع المستودع إلى GitHub.
2. في Render: **New → Blueprint** واختر المستودع (يقرأ `render.yaml`).
3. ضع الأسرار في **Environment** (لا تضعها في الملفات):
   - `OPENAI_API_KEY`
   - `MINBAR_BROADCAST_CODES` مثل `KHATAM-2026=رمز-قوي-خاص-بك`
   - `MINBAR_ALLOWED_ORIGINS` اختياري (مثلًا `https://minbar.onrender.com` إذا احتاجته أداة خارجية)
4. `MINBAR_ENV=production` مضبوط في `render.yaml`.
5. فحص الصحة `GET /ready`: يعيد 503 حتى يُضبط المفتاح والرموز، فلا يُفتح رابط ناقص الإعداد.

Render يوفّر HTTPS، والواجهة تتصل بـ `wss://` تلقائيًا. خيار `--proxy-headers` يجعل التطبيق يرى أن الطلب https فيضيف HSTS.

> الحالة في الذاكرة، فأبقِ نسخة واحدة (`numInstances: 1`). الخطة المجانية تُطفئ الخدمة عند الخمول فتضيع حالة الغرف؛ استخدم خطة مدفوعة للبث الفعلي، أو افتح الرابط قبل الخطبة بدقائق.

## 2. Docker

```bash
docker build -t minbar .
docker run -p 10000:10000 \
  -e OPENAI_API_KEY=... \
  -e MINBAR_BROADCAST_CODES="KHATAM-2026=..." \
  minbar
```

الصورة تعمل بمستخدم غير root، وفيها `HEALTHCHECK` على `/health`. ضعها خلف وكيل TLS (Nginx/Caddy/منصة سحابية) يمرّر WebSocket.

## 3. إضافة جامع

1. أضف عنصرًا إلى `data/mosques.json`: `{"id": "ROOM-ID", "name": "...", "location": "..."}`.
2. أضف رمزه السري إلى `MINBAR_BROADCAST_CODES`: `KHATAM-2026=...,ROOM-ID=...`.
3. رابط المصلين: `https://YOUR-DOMAIN/listen?room=ROOM-ID` (بدون `room` يُستخدم أول جامع).

## 4. قائمة فحص بعد النشر

- [ ] `GET /ready` = 200 و `"openai_configured": true` و `"broadcast_codes_configured": true`
- [ ] `/broadcast`: رمز خاطئ ← «الرمز غير صحيح.»
- [ ] بث تجريبي من جوال، واستماع من جهاز وشبكة أخرى
- [ ] آية معروفة (مثل آل عمران 102) تظهر ببطاقة ذهبية وترجمة QuranEnc
- [ ] إيقاف البث ← المستمعون يرون «انتهت الخطبة» وإعادة القراءة تعمل
- [ ] لا يوجد `.env` ولا تسجيلات في المستودع (`git ls-files | grep -iE "\.env$|\.mp3|\.wav|\.m4a"` فارغ)

## الخصوصية

لا قاعدة بيانات للمصلين. حالة الغرف ونصوص إعادة القراءة في الذاكرة فقط، وتُحذف بعد `MINBAR_ROOM_TTL_SECONDS` من انتهاء البث. الصوت المرفوع يُكتب في ملف مؤقت لطلب التحويل ويُحذف بعده مباشرة.
