# حالة الخادم — Backend status

هذا المستند كان يسرد ما تحتاجه الواجهة من الخادم في النموذج الأولي. كل البنود منفّذة الآن:

| الحاجة | التنفيذ |
|---|---|
| عدد المستمعين عند الانضمام والمغادرة | `listeners` عبر WebSocket للمذيع، مع العدد لكل لغة (`realtime/manager.py`) |
| رسائل بدء البث وانتهائه | `started` و `ended`، والحالة `READY/LIVE/ENDED` |
| كشف الآيات | `POST /detect_verse` وداخل كل مقطع (`services/verse_service.py`) |
| الترجمة الموثقة للآيات | من `data/translations/*.json` مع المصدر والمترجم والإصدار |
| التحقق من رمز الجامع | `POST /broadcast/verify` و `/broadcast/start`؛ الجوامع في `data/mosques.json` والرموز السرية في `MINBAR_BROADCAST_CODES` |
| رمز جلسة المذيع | `broadcaster_token` لكل بث، مطلوب للصوت والإيقاف |
| ترجمة اللغات الثلاث | داخل كل مقطع بالتوازي (`services/pipeline.py`) |
| إعادة الاتصال | `since` و `session` في WebSocket دون تكرار |
| إعادة القراءة | `GET /broadcast/{room}/replay` |
| الخطب المسجلة | `POST /live/{room}/recorded` في الخلفية مع التقدّم |
| عدم الاعتماد على localhost | الواجهة تستخدم `location.origin` و `wss://` على https |

العقد الكامل في [contract.md](contract.md).
