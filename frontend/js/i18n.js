// Interface language (i18n) for every Minbar page.
//
// - Static text:   <el data-i18n="key">, data-i18n-placeholder, data-i18n-aria-label, data-i18n-title
// - Dynamic text:  I18N.t('key', {var: value})
// - Server errors: I18N.error(code, fallbackMessage)
// - Switcher:      <div data-ui-lang></div> placeholders become the language menu
// - Changes fire a 'minbar:lang' event on window; pages re-render dynamic parts.
//
// The interface language is stored in localStorage on this device only. It is
// independent from the sermon translation language chosen on the listener page.
(function () {
  const LANGS = {
    ar: {name: 'العربية', dir: 'rtl', flag: 'flag-sa', locale: 'ar-SA-u-nu-latn'},
    en: {name: 'English', dir: 'ltr', flag: 'flag-gb', locale: 'en-US'},
    ur: {name: 'اردو', dir: 'rtl', flag: 'flag-pk', locale: 'ur-PK'},
    hi: {name: 'हिन्दी', dir: 'ltr', flag: 'flag-in', locale: 'hi-IN'},
  };
  const ORDER = ['ar', 'en', 'ur', 'hi'];
  const KEY = 'minbar.ui';

  const M = {
    ar: {
      'ui.language': 'لغة الواجهة',
      'common.back': 'العودة',
      'common.privacy': 'سياسة الخصوصية',
      'common.mb': 'ميغابايت',

      'title.home': 'منبر — افهم خطبة الجمعة بلغتك',
      'title.listen': 'منبر — المصلّي',
      'title.broadcast': 'منبر — صفحة البث',
      'title.privacy': 'منبر — الخصوصية',

      'home.headline': 'افهم خطبة الجمعة بلغتك',
      'home.desc': 'منبر يتيح لك الاستماع إلى خطبة الجمعة مترجمة بعدة لغات، ليربطك بقيم الجمعة ومعانيها.',
      'home.worshipper': 'أنا مصلٍّ',
      'home.supervisor': 'دخول مشرفي الجوامع',

      'listen.start': 'ابدأ',
      'listen.chooseTitle': 'اختر لغتك',
      'listen.chooseSub': 'لغة ترجمة الخطبة',
      'listen.arabicNote': '(نص الخطبة)',
      'listen.arabicSub': 'لضعاف السمع',
      'listen.continue': 'متابعة',
      'listen.sessionNote': 'لن تحتاج لاختيار لغتك مرة أخرى خلال هذه الجلسة.',
      'listen.sermonLanguage': 'لغة ترجمة الخطبة',
      'listen.waiting': 'الخطبة لم تبدأ بعد.',
      'listen.waitingSub': 'أبقِ الصفحة مفتوحة، وستظهر الترجمة تلقائياً.',
      'listen.connected': 'متصل',
      'listen.connecting': 'جارٍ الاتصال…',
      'listen.disconnected': 'انقطع الاتصال',
      'listen.live': 'مباشر',
      'listen.disc': 'انقطع الاتصال، جارٍ إعادة الاتصال.',
      'listen.discSub': 'لن يفوتك شيء.',
      'listen.disclaimerTranslation': 'ترجمة آلية بالذكاء الاصطناعي، والمرجع كلام الخطيب.',
      'listen.disclaimerTranscript': 'نص آلي من كلام الخطيب، قد يحتوي أخطاء.',
      'listen.feedTitle': 'سجل الخطبة',
      'listen.now': 'الآن',
      'listen.quran': 'قرآن',
      'listen.hadith': 'حديث كما ذكره الخطيب',
      'listen.unclear': 'غير واضح',
      'listen.unclearText': 'لم يتم التعرف على هذا الجزء من الخطبة بوضوح.',
      'listen.sura': 'سورة',
      'listen.quranSource': 'النص القرآني: مجمع الملك فهد لطباعة المصحف الشريف',
      'listen.translationOf': 'ترجمة معاني القرآن الكريم',
      'listen.failNote': 'تعذّرت الترجمة الآلية لهذا الجزء، ويظهر النص العربي.',
      'listen.latest': 'آخر الخطبة',
      'listen.fontUp': 'تكبير الخط',
      'listen.fontDown': 'تصغير الخط',
      'listen.ended': 'انتهت الخطبة.',
      'listen.dua': 'تقبّل الله منا ومنكم.',
      'listen.rating': 'ما مدى وضوح الترجمة؟',
      'listen.thanks': 'شكرًا لك.',
      'listen.replay': 'إعادة قراءة الخطبة',
      'listen.replayEmpty': 'لا توجد نسخة مؤقتة من الخطبة.',
      'listen.replayFailed': 'تعذّر تحميل الخطبة.',
      'listen.unknownRoom': 'رابط الجامع غير صحيح.',

      'bc.title': 'صفحة البث',
      'bc.sub': 'للمؤذن أو مشرف الجامع.',
      'bc.mosque': 'اختيار الجامع',
      'bc.code': 'رمز البث',
      'bc.showCode': 'إظهار الرمز',
      'bc.login': 'دخول',
      'bc.khateeb': 'الخطيب',
      'bc.khateebNone': 'غير محدد',
      'bc.khateebHint': 'الخطيب لا يحتاج أن يلمس الجهاز.',
      'bc.enterCode': 'أدخل رمز البث.',
      'bc.verifyFailed': 'تعذّر التحقق من الرمز.',
      'bc.ready': 'جاهز للبث',
      'bc.mic': 'الميكروفون',
      'bc.file': 'ملف صوتي',
      'bc.micPreparing': 'جارٍ تجهيز الميكروفون…',
      'bc.micSpeak': 'تحدّث قرب الجهاز لاختبار الميكروفون',
      'bc.micWorks': 'الميكروفون يعمل',
      'bc.micNotFound': 'لم يُعثر على ميكروفون في هذا الجهاز.',
      'bc.micFailed': 'تعذّر تشغيل الميكروفون.',
      'bc.fileHint': 'خطبة مسجلة حتى {max} ميغابايت (MP3, M4A, WAV, OGG, WEBM).',
      'bc.fileInfo': '{name} — {size} ميغابايت',
      'bc.fileTooBigInfo': 'حجم الملف {size} ميغابايت ويتجاوز الحد ({max} ميغابايت).',
      'bc.waiting': 'المصلون بانتظار الخطبة',
      'bc.worshippers': 'مصلٍّ',
      'bc.tip': 'ضع الجهاز قرب الخطيب، ولا تقفل الشاشة.',
      'bc.start': 'ابدأ البث',
      'bc.logout': 'تسجيل الخروج',
      'bc.alreadyLiveHint': 'البث قائم الآن في هذا الجامع. اضغط «ابدأ البث» لمتابعته من هذا الجهاز.',
      'bc.speechOff': 'لا يمكن بدء بث صوتي: خدمة التعرف على الكلام غير مُعدّة على الخادم. أضف OPENAI_API_KEY إلى ملف .env ثم أعد تشغيل الخادم.',
      'bc.chooseFile': 'اختر ملفًا صوتيًا أولًا.',
      'bc.fileTooBig': 'حجم الملف يتجاوز الحد المسموح.',
      'bc.confirmResume': 'البث قائم بالفعل في هذا الجامع. هل تريد متابعته من هذا الجهاز؟',
      'bc.startFailed': 'تعذّر بدء البث.',
      'bc.deniedTitle': 'نحتاج إذن الميكروفون',
      'bc.insecureTitle': 'يتطلب الميكروفون اتصالًا آمنًا',
      'bc.step1': 'افتح «الإعدادات» في iPhone أو iPad ثم اختر «Safari».',
      'bc.step2': 'اختر «الميكروفون» من قسم إعدادات المواقع.',
      'bc.step3': 'اختر «السماح»، ثم عد إلى هذه الصفحة واضغط «حاول مرة أخرى».',
      'bc.insecureHint': 'الميكروفون يتطلب فتح منبر عبر رابط آمن يبدأ بـ https://',
      'bc.retry': 'حاول مرة أخرى',
      'bc.uploadInstead': 'ارفع خطبة مسجلة',
      'bc.liveNow': 'يبث الآن',
      'bc.recorded': 'الخطبة المسجلة',
      'bc.uploading': 'جارٍ رفع الملف…',
      'bc.uploadOther': 'ارفع ملفًا آخر',
      'bc.detected': 'النص العربي المكتشف',
      'bc.waitingFirst': 'بانتظار أول مقطع…',
      'bc.unclearMarker': '— غير واضح —',
      'bc.listeners': 'المستمعون',
      'bc.listenerUnit': 'مستمع',
      'bc.stop': 'إيقاف البث',
      'bc.confirmStop': 'هل تريد إيقاف البث؟',
      'bc.stopping': 'جارٍ إرسال آخر مقطع وإيقاف البث…',
      'bc.stopFailed': 'تعذّر إيقاف البث.',
      'bc.stopOffline': 'تعذّر الاتصال بالخادم لإيقاف البث. حاول مرة أخرى.',
      'bc.lastChunk': 'آخر مقطع قبل {n} ثوانٍ',
      'bc.chunkUnclear': 'مقطع غير واضح، يستمر البث.',
      'bc.chunkRetry': 'تعذّرت معالجة المقطع، تتم إعادة المحاولة…',
      'bc.chunkSkipped': 'تعذّرت معالجة المقطع، يستمر البث مع المقطع التالي.',
      'bc.chunkOffline': 'انقطع الاتصال بالخادم، سيُعاد الإرسال تلقائيًا…',
      'bc.slowNetwork': 'الشبكة بطيئة، تم تجاوز مقطع قديم.',
      'bc.sessionEnded': 'انتهت جلسة البث.',
      'bc.sessionMoved': 'انتقل البث إلى جهاز آخر أو انتهت الجلسة.',
      'bc.uploadFailed': 'تعذّر رفع الخطبة.',
      'bc.uploadDropped': 'انقطع الاتصال أثناء رفع الملف.',
      'bc.transcribing': 'جارٍ تحويل الصوت إلى نص…',
      'bc.translating': 'جارٍ الترجمة والنشر: {n} من {total}',
      'bc.processed': 'اكتملت المعالجة: {n} مقطعًا وصلت إلى المصلين.',
      'bc.processedHint': 'يمكنك إيقاف البث عندما ينتهي المصلون من القراءة.',
      'bc.ended': 'انتهى البث، جزاك الله خيراً.',
      'bc.duration': 'مدة البث',
      'bc.peak': 'أعلى عدد مستمعين',
      'bc.verses': 'الآيات المعتمدة',
      'bc.unclearSegments': 'مقاطع غير واضحة',
      'bc.newBroadcast': 'بث جديد',
      'bc.viewTranscript': 'عرض نص الخطبة',

      'privacy.title': 'الخصوصية وحماية البيانات',
      'privacy.subtitle': 'Privacy Policy',
      'privacy.noDataTitle': 'لا نجمع بيانات المصلين',
      'privacy.noData1': 'لا نطلب اسمًا ولا رقم جوال ولا بريدًا إلكترونيًا، ولا توجد قاعدة بيانات للمصلين.',
      'privacy.noData2': 'عدد المستمعين يُحسب لحظيًا في ذاكرة الخادم فقط، دون أي معرّف شخصي.',
      'privacy.noData3': 'لغة الواجهة تُحفظ في متصفحك على هذا الجهاز فقط، ولغة ترجمة الخطبة تُحفظ خلال الجلسة الحالية فقط، ولا يُخزَّن أيٌّ منهما على الخادم.',
      'privacy.noAudioTitle': 'لا نسجّل أصوات المصلين',
      'privacy.noAudio1': 'جهاز المصلّي لا يرسل أي صوت؛ هو يستقبل النص فقط.',
      'privacy.noAccountTitle': 'لا نحتاج حسابًا',
      'privacy.noAccount1': 'تفتح الرابط وتختار لغتك، دون تسجيل أو كلمة مرور.',
      'privacy.khateebTitle': 'صوت الخطيب يُعالج للترجمة ولا يُحفظ',
      'privacy.khateeb1': 'يُرسل كل مقطع صوتي إلى خدمة تحويل الكلام إلى نص (OpenAI) ثم يُحذف الملف المؤقت فور انتهاء المعالجة.',
      'privacy.khateeb2': 'نص الخطبة وترجمتها يبقيان في ذاكرة الخادم مؤقتًا لإتاحة إعادة القراءة، ثم يُحذفان تلقائيًا بعد ساعتين من انتهاء البث.',
      'privacy.khateeb3': 'الآيات القرآنية تُعرض بترجماتها الموثقة من QuranEnc، وبقية الكلام ترجمة آلية قد تحتوي أخطاء، والمرجع كلام الخطيب.',

      'err.offline': 'تعذّر الوصول إلى خادم منبر. افتح الصفحة من الخادم نفسه (مثل http://127.0.0.1:8000/broadcast)، أو أضف ?api=http://127.0.0.1:8765 إلى الرابط.',
      'err.generic': 'حدث خطأ. حاول مرة أخرى.',
      'err.invalid_code': 'الرمز غير صحيح.',
      'err.missing_code': 'أدخل رمز البث.',
      'err.unknown_mosque': 'الجامع غير موجود.',
      'err.unknown_room': 'الجامع غير موجود.',
      'err.codes_not_configured': 'رمز البث غير مُعدّ لهذا الجامع.',
      'err.already_live': 'البث قائم بالفعل في هذا الجامع.',
      'err.already_ended': 'انتهى البث بالفعل.',
      'err.not_live': 'البث غير قائم.',
      'err.unauthorized': 'جلسة البث غير مصرح بها.',
      'err.processing': 'جارٍ معالجة خطبة مسجلة في هذا الجامع.',
      'err.empty_audio': 'المقطع الصوتي فارغ.',
      'err.unsupported_audio': 'صيغة الملف غير مدعومة. الصيغ المدعومة: MP3, M4A, WAV, WEBM, OGG, MP4, FLAC.',
      'err.file_too_large': 'حجم الملف يتجاوز الحد المسموح.',
      'err.audio_processing_failed': 'تعذّرت معالجة الصوت مؤقتًا. ستستمر المحاولة مع المقطع التالي.',
      'err.ai_unavailable': 'خدمة التعرف على الكلام غير مُعدّة على الخادم. أضف OPENAI_API_KEY إلى ملف .env ثم أعد تشغيل الخادم.',
      'err.ai_key_invalid': 'مفتاح OpenAI على الخادم غير صالح أو بلا صلاحية. حدّث OPENAI_API_KEY ثم أعد تشغيل الخادم.',
      'err.translation_failed': 'تعذّرت الترجمة الآلية مؤقتًا.',
      'err.unsupported_language': 'اللغة غير مدعومة.',
      'err.unclear_text': 'النص لا يحتوي على كلام عربي واضح.',
      'err.no_arabic_speech': 'لم يُتعرّف على كلام عربي واضح في الملف.',
      'err.recorded_failed': 'تعذّرت معالجة الخطبة المسجلة.',
      'err.server_error': 'حدث خطأ غير متوقع في الخادم.',
    },

    en: {
      'ui.language': 'Interface language',
      'common.back': 'Back',
      'common.privacy': 'Privacy policy',
      'common.mb': 'MB',

      'title.home': 'Minbar — Understand the Friday sermon in your language',
      'title.listen': 'Minbar — Worshipper',
      'title.broadcast': 'Minbar — Broadcast',
      'title.privacy': 'Minbar — Privacy',

      'home.headline': 'Understand the Friday sermon in your language',
      'home.desc': 'Minbar lets you follow the Friday sermon translated into several languages, connecting you with its values and meanings.',
      'home.worshipper': 'I’m a worshipper',
      'home.supervisor': 'Mosque supervisors',

      'listen.start': 'Start',
      'listen.chooseTitle': 'Choose your language',
      'listen.chooseSub': 'Sermon translation language',
      'listen.arabicNote': '(sermon text)',
      'listen.arabicSub': 'For the hard of hearing',
      'listen.continue': 'Continue',
      'listen.sessionNote': 'You won’t need to choose again during this session.',
      'listen.sermonLanguage': 'Sermon translation language',
      'listen.waiting': 'The sermon has not started yet.',
      'listen.waitingSub': 'Keep this page open. The translation will appear automatically.',
      'listen.connected': 'Connected',
      'listen.connecting': 'Connecting…',
      'listen.disconnected': 'Disconnected',
      'listen.live': 'LIVE',
      'listen.disc': 'Connection lost. Reconnecting…',
      'listen.discSub': 'You won’t miss anything.',
      'listen.disclaimerTranslation': 'AI machine translation. The khateeb’s words are the reference.',
      'listen.disclaimerTranscript': 'Automatic transcript of the khateeb’s words; it may contain errors.',
      'listen.feedTitle': 'Sermon log',
      'listen.now': 'Now',
      'listen.quran': 'Quran',
      'listen.hadith': 'Hadith as cited by the khateeb',
      'listen.unclear': 'Unclear',
      'listen.unclearText': 'This part of the sermon could not be recognized clearly.',
      'listen.sura': 'Surah',
      'listen.quranSource': 'Quran text: King Fahd Glorious Quran Printing Complex',
      'listen.translationOf': 'Translation of the meanings of the Noble Qur’an',
      'listen.failNote': 'Machine translation is unavailable for this part; the Arabic text is shown.',
      'listen.latest': 'Latest',
      'listen.fontUp': 'Larger text',
      'listen.fontDown': 'Smaller text',
      'listen.ended': 'The sermon has ended.',
      'listen.dua': 'May Allah accept from us and from you.',
      'listen.rating': 'How clear was the translation?',
      'listen.thanks': 'Thank you.',
      'listen.replay': 'Read the sermon again',
      'listen.replayEmpty': 'No temporary copy of the sermon is available.',
      'listen.replayFailed': 'Could not load the sermon.',
      'listen.unknownRoom': 'This mosque link is not valid.',

      'bc.title': 'Broadcast',
      'bc.sub': 'For the muezzin or mosque supervisor.',
      'bc.mosque': 'Mosque',
      'bc.code': 'Broadcast code',
      'bc.showCode': 'Show code',
      'bc.login': 'Sign in',
      'bc.khateeb': 'Khateeb',
      'bc.khateebNone': 'Not specified',
      'bc.khateebHint': 'The khateeb doesn’t need to touch the device.',
      'bc.enterCode': 'Enter the broadcast code.',
      'bc.verifyFailed': 'Could not verify the code.',
      'bc.ready': 'Ready to broadcast',
      'bc.mic': 'Microphone',
      'bc.file': 'Audio file',
      'bc.micPreparing': 'Preparing the microphone…',
      'bc.micSpeak': 'Speak near the device to test the microphone',
      'bc.micWorks': 'The microphone is working',
      'bc.micNotFound': 'No microphone was found on this device.',
      'bc.micFailed': 'Could not start the microphone.',
      'bc.fileHint': 'Recorded sermon up to {max} MB (MP3, M4A, WAV, OGG, WEBM).',
      'bc.fileInfo': '{name} — {size} MB',
      'bc.fileTooBigInfo': 'The file is {size} MB, which exceeds the {max} MB limit.',
      'bc.waiting': 'Worshippers waiting for the sermon',
      'bc.worshippers': 'worshippers',
      'bc.tip': 'Place the device near the khateeb and keep the screen on.',
      'bc.start': 'Start broadcast',
      'bc.logout': 'Sign out',
      'bc.alreadyLiveHint': 'A broadcast is already live at this mosque. Press “Start broadcast” to continue it from this device.',
      'bc.speechOff': 'An audio broadcast can’t start: speech recognition isn’t configured on the server. Add OPENAI_API_KEY to the .env file, then restart the server.',
      'bc.chooseFile': 'Choose an audio file first.',
      'bc.fileTooBig': 'The file exceeds the size limit.',
      'bc.confirmResume': 'A broadcast is already live at this mosque. Continue it from this device?',
      'bc.startFailed': 'Could not start the broadcast.',
      'bc.deniedTitle': 'Microphone permission needed',
      'bc.insecureTitle': 'The microphone needs a secure connection',
      'bc.step1': 'Open “Settings” on your iPhone or iPad, then choose “Safari”.',
      'bc.step2': 'Choose “Microphone” under website settings.',
      'bc.step3': 'Choose “Allow”, then come back to this page and tap “Try again”.',
      'bc.insecureHint': 'The microphone only works when Minbar is opened over a secure link starting with https://',
      'bc.retry': 'Try again',
      'bc.uploadInstead': 'Upload a recorded sermon',
      'bc.liveNow': 'Live now',
      'bc.recorded': 'Recorded sermon',
      'bc.uploading': 'Uploading the file…',
      'bc.uploadOther': 'Upload another file',
      'bc.detected': 'Detected Arabic text',
      'bc.waitingFirst': 'Waiting for the first segment…',
      'bc.unclearMarker': '— unclear —',
      'bc.listeners': 'Listeners',
      'bc.listenerUnit': 'listeners',
      'bc.stop': 'Stop broadcast',
      'bc.confirmStop': 'Stop the broadcast?',
      'bc.stopping': 'Sending the last segment and stopping…',
      'bc.stopFailed': 'Could not stop the broadcast.',
      'bc.stopOffline': 'Could not reach the server to stop the broadcast. Try again.',
      'bc.lastChunk': 'Last segment {n} s ago',
      'bc.chunkUnclear': 'Unclear segment; the broadcast continues.',
      'bc.chunkRetry': 'A segment couldn’t be processed; retrying…',
      'bc.chunkSkipped': 'A segment couldn’t be processed; continuing with the next one.',
      'bc.chunkOffline': 'Lost connection to the server; segments will be resent automatically…',
      'bc.slowNetwork': 'The network is slow; an old segment was skipped.',
      'bc.sessionEnded': 'The broadcast session has ended.',
      'bc.sessionMoved': 'The broadcast moved to another device or the session ended.',
      'bc.uploadFailed': 'Could not upload the sermon.',
      'bc.uploadDropped': 'The connection dropped while uploading the file.',
      'bc.transcribing': 'Converting speech to text…',
      'bc.translating': 'Translating and publishing: {n} of {total}',
      'bc.processed': 'Processing complete: {n} segments reached the worshippers.',
      'bc.processedHint': 'You can stop the broadcast once worshippers have finished reading.',
      'bc.ended': 'The broadcast has ended. May Allah reward you.',
      'bc.duration': 'Duration',
      'bc.peak': 'Peak listeners',
      'bc.verses': 'Verified verses',
      'bc.unclearSegments': 'Unclear segments',
      'bc.newBroadcast': 'New broadcast',
      'bc.viewTranscript': 'View the transcript',

      'privacy.title': 'Privacy and data protection',
      'privacy.subtitle': 'الخصوصية وحماية البيانات',
      'privacy.noDataTitle': 'We don’t collect worshippers’ data',
      'privacy.noData1': 'We don’t ask for a name, phone number or email, and there is no worshipper database.',
      'privacy.noData2': 'The number of listeners is counted live in server memory only, without any personal identifier.',
      'privacy.noData3': 'The interface language is saved in your browser on this device only, and the sermon translation language only for the current session. Neither is stored on the server.',
      'privacy.noAudioTitle': 'We don’t record worshippers’ voices',
      'privacy.noAudio1': 'The worshipper’s device sends no audio; it only receives text.',
      'privacy.noAccountTitle': 'No account needed',
      'privacy.noAccount1': 'Open the link and choose your language — no sign-up, no password.',
      'privacy.khateebTitle': 'The khateeb’s audio is processed for translation, not stored',
      'privacy.khateeb1': 'Each audio segment is sent to a speech-to-text service (OpenAI), and the temporary file is deleted as soon as processing ends.',
      'privacy.khateeb2': 'The sermon text and its translation stay in server memory temporarily for replay, and are deleted automatically two hours after the broadcast ends.',
      'privacy.khateeb3': 'Quranic verses are shown with verified translations from QuranEnc; the rest is machine translation that may contain errors, with the khateeb’s words as the reference.',

      'err.offline': 'Can’t reach the Minbar server. Open the page from the server itself (e.g. http://127.0.0.1:8000/broadcast), or add ?api=http://127.0.0.1:8765 to the link.',
      'err.generic': 'Something went wrong. Please try again.',
      'err.invalid_code': 'The code is incorrect.',
      'err.missing_code': 'Enter the broadcast code.',
      'err.unknown_mosque': 'Mosque not found.',
      'err.unknown_room': 'Mosque not found.',
      'err.codes_not_configured': 'No broadcast code is configured for this mosque.',
      'err.already_live': 'A broadcast is already live at this mosque.',
      'err.already_ended': 'The broadcast has already ended.',
      'err.not_live': 'The broadcast is not live.',
      'err.unauthorized': 'This broadcast session is not authorized.',
      'err.processing': 'A recorded sermon is being processed at this mosque.',
      'err.empty_audio': 'The audio segment is empty.',
      'err.unsupported_audio': 'Unsupported file format. Supported: MP3, M4A, WAV, WEBM, OGG, MP4, FLAC.',
      'err.file_too_large': 'The file exceeds the size limit.',
      'err.audio_processing_failed': 'Audio processing is temporarily unavailable. The next segment will be tried.',
      'err.ai_unavailable': 'Speech recognition isn’t configured on the server. Add OPENAI_API_KEY to the .env file, then restart the server.',
      'err.ai_key_invalid': 'The OpenAI key on the server is invalid or lacks permission. Update OPENAI_API_KEY, then restart the server.',
      'err.translation_failed': 'Machine translation is temporarily unavailable.',
      'err.unsupported_language': 'Unsupported language.',
      'err.unclear_text': 'The text contains no clear Arabic speech.',
      'err.no_arabic_speech': 'No clear Arabic speech was recognized in the file.',
      'err.recorded_failed': 'The recorded sermon could not be processed.',
      'err.server_error': 'An unexpected server error occurred.',
    },

    ur: {
      'ui.language': 'انٹرفیس کی زبان',
      'common.back': 'واپس',
      'common.privacy': 'رازداری کی پالیسی',
      'common.mb': 'ایم بی',

      'title.home': 'منبر — جمعہ کا خطبہ اپنی زبان میں سمجھیں',
      'title.listen': 'منبر — نمازی',
      'title.broadcast': 'منبر — نشریات',
      'title.privacy': 'منبر — رازداری',

      'home.headline': 'جمعہ کا خطبہ اپنی زبان میں سمجھیں',
      'home.desc': 'منبر آپ کو جمعہ کا خطبہ کئی زبانوں میں ترجمے کے ساتھ سننے کی سہولت دیتا ہے، تاکہ آپ جمعہ کی اقدار اور معانی سے جڑ سکیں۔',
      'home.worshipper': 'میں نمازی ہوں',
      'home.supervisor': 'مسجد کے نگران کا داخلہ',

      'listen.start': 'شروع کریں',
      'listen.chooseTitle': 'اپنی زبان منتخب کریں',
      'listen.chooseSub': 'خطبے کے ترجمے کی زبان',
      'listen.arabicNote': '(خطبے کا متن)',
      'listen.arabicSub': 'کم سننے والوں کے لیے',
      'listen.continue': 'جاری رکھیں',
      'listen.sessionNote': 'اس سیشن کے دوران آپ کو دوبارہ زبان منتخب نہیں کرنی پڑے گی۔',
      'listen.sermonLanguage': 'خطبے کے ترجمے کی زبان',
      'listen.waiting': 'خطبہ ابھی شروع نہیں ہوا۔',
      'listen.waitingSub': 'یہ صفحہ کھلا رکھیں، ترجمہ خود بخود ظاہر ہوگا۔',
      'listen.connected': 'منسلک',
      'listen.connecting': 'منسلک ہو رہا ہے…',
      'listen.disconnected': 'رابطہ منقطع',
      'listen.live': 'براہِ راست',
      'listen.disc': 'رابطہ منقطع ہو گیا، دوبارہ جوڑا جا رہا ہے۔',
      'listen.discSub': 'آپ سے کچھ نہیں چھوٹے گا۔',
      'listen.disclaimerTranslation': 'مصنوعی ذہانت کے ذریعے خودکار ترجمہ، اصل حوالہ خطیب کا کلام ہے۔',
      'listen.disclaimerTranscript': 'خطیب کے کلام کا خودکار متن، اس میں غلطیاں ہو سکتی ہیں۔',
      'listen.feedTitle': 'خطبے کا ریکارڈ',
      'listen.now': 'ابھی',
      'listen.quran': 'قرآن',
      'listen.hadith': 'حدیث، جیسا کہ خطیب نے بیان کی',
      'listen.unclear': 'غیر واضح',
      'listen.unclearText': 'خطبے کا یہ حصہ واضح طور پر پہچانا نہیں جا سکا۔',
      'listen.sura': 'سورۃ',
      'listen.quranSource': 'قرآنی متن: شاہ فہد قرآن پرنٹنگ کمپلیکس',
      'listen.translationOf': 'قرآن کریم کے معانی کا ترجمہ',
      'listen.failNote': 'اس حصے کا خودکار ترجمہ دستیاب نہیں، عربی متن دکھایا جا رہا ہے۔',
      'listen.latest': 'تازہ ترین',
      'listen.fontUp': 'متن بڑا کریں',
      'listen.fontDown': 'متن چھوٹا کریں',
      'listen.ended': 'خطبہ ختم ہو گیا۔',
      'listen.dua': 'اللہ ہم سے اور آپ سے قبول فرمائے۔',
      'listen.rating': 'ترجمہ کتنا واضح تھا؟',
      'listen.thanks': 'شکریہ۔',
      'listen.replay': 'خطبہ دوبارہ پڑھیں',
      'listen.replayEmpty': 'خطبے کی کوئی عارضی کاپی دستیاب نہیں۔',
      'listen.replayFailed': 'خطبہ لوڈ نہیں ہو سکا۔',
      'listen.unknownRoom': 'مسجد کا یہ لنک درست نہیں۔',

      'bc.title': 'نشریات کا صفحہ',
      'bc.sub': 'مؤذن یا مسجد کے نگران کے لیے۔',
      'bc.mosque': 'مسجد منتخب کریں',
      'bc.code': 'نشریاتی کوڈ',
      'bc.showCode': 'کوڈ دکھائیں',
      'bc.login': 'داخل ہوں',
      'bc.khateeb': 'خطیب',
      'bc.khateebNone': 'متعین نہیں',
      'bc.khateebHint': 'خطیب کو آلے کو چھونے کی ضرورت نہیں۔',
      'bc.enterCode': 'نشریاتی کوڈ درج کریں۔',
      'bc.verifyFailed': 'کوڈ کی تصدیق نہیں ہو سکی۔',
      'bc.ready': 'نشریات کے لیے تیار',
      'bc.mic': 'مائیکروفون',
      'bc.file': 'آڈیو فائل',
      'bc.micPreparing': 'مائیکروفون تیار ہو رہا ہے…',
      'bc.micSpeak': 'مائیکروفون جانچنے کے لیے آلے کے قریب بولیں',
      'bc.micWorks': 'مائیکروفون کام کر رہا ہے',
      'bc.micNotFound': 'اس آلے میں کوئی مائیکروفون نہیں ملا۔',
      'bc.micFailed': 'مائیکروفون شروع نہیں ہو سکا۔',
      'bc.fileHint': 'ریکارڈ شدہ خطبہ، زیادہ سے زیادہ {max} ایم بی (MP3, M4A, WAV, OGG, WEBM)۔',
      'bc.fileInfo': '{name} — {size} ایم بی',
      'bc.fileTooBigInfo': 'فائل کا سائز {size} ایم بی ہے جو حد ({max} ایم بی) سے زیادہ ہے۔',
      'bc.waiting': 'خطبے کے منتظر نمازی',
      'bc.worshippers': 'نمازی',
      'bc.tip': 'آلہ خطیب کے قریب رکھیں اور اسکرین بند نہ کریں۔',
      'bc.start': 'نشریات شروع کریں',
      'bc.logout': 'لاگ آؤٹ',
      'bc.alreadyLiveHint': 'اس مسجد میں نشریات پہلے سے جاری ہیں۔ اس آلے سے جاری رکھنے کے لیے «نشریات شروع کریں» دبائیں۔',
      'bc.speechOff': 'آڈیو نشریات شروع نہیں ہو سکتیں: سرور پر تقریر کی شناخت کی سروس ترتیب نہیں دی گئی۔ ‎.env فائل میں OPENAI_API_KEY شامل کریں، پھر سرور دوبارہ شروع کریں۔',
      'bc.chooseFile': 'پہلے آڈیو فائل منتخب کریں۔',
      'bc.fileTooBig': 'فائل کا سائز حد سے زیادہ ہے۔',
      'bc.confirmResume': 'اس مسجد میں نشریات پہلے سے جاری ہیں۔ کیا اس آلے سے جاری رکھیں؟',
      'bc.startFailed': 'نشریات شروع نہیں ہو سکیں۔',
      'bc.deniedTitle': 'مائیکروفون کی اجازت درکار ہے',
      'bc.insecureTitle': 'مائیکروفون کے لیے محفوظ کنکشن ضروری ہے',
      'bc.step1': 'iPhone یا iPad میں «Settings» کھولیں، پھر «Safari» منتخب کریں۔',
      'bc.step2': 'ویب سائٹ کی ترتیبات میں «Microphone» منتخب کریں۔',
      'bc.step3': '«Allow» منتخب کریں، پھر اس صفحے پر واپس آ کر «دوبارہ کوشش کریں» دبائیں۔',
      'bc.insecureHint': 'مائیکروفون صرف اسی وقت کام کرتا ہے جب منبر https:// سے شروع ہونے والے محفوظ لنک سے کھولا جائے۔',
      'bc.retry': 'دوبارہ کوشش کریں',
      'bc.uploadInstead': 'ریکارڈ شدہ خطبہ اپلوڈ کریں',
      'bc.liveNow': 'براہِ راست نشر',
      'bc.recorded': 'ریکارڈ شدہ خطبہ',
      'bc.uploading': 'فائل اپلوڈ ہو رہی ہے…',
      'bc.uploadOther': 'دوسری فائل اپلوڈ کریں',
      'bc.detected': 'شناخت شدہ عربی متن',
      'bc.waitingFirst': 'پہلے حصے کا انتظار…',
      'bc.unclearMarker': '— غیر واضح —',
      'bc.listeners': 'سامعین',
      'bc.listenerUnit': 'سامع',
      'bc.stop': 'نشریات روکیں',
      'bc.confirmStop': 'کیا نشریات روک دیں؟',
      'bc.stopping': 'آخری حصہ بھیجا جا رہا ہے اور نشریات روکی جا رہی ہیں…',
      'bc.stopFailed': 'نشریات روکی نہیں جا سکیں۔',
      'bc.stopOffline': 'نشریات روکنے کے لیے سرور سے رابطہ نہیں ہو سکا۔ دوبارہ کوشش کریں۔',
      'bc.lastChunk': 'آخری حصہ {n} سیکنڈ پہلے',
      'bc.chunkUnclear': 'غیر واضح حصہ، نشریات جاری ہیں۔',
      'bc.chunkRetry': 'حصے پر کارروائی نہیں ہو سکی، دوبارہ کوشش ہو رہی ہے…',
      'bc.chunkSkipped': 'حصے پر کارروائی نہیں ہو سکی، اگلے حصے کے ساتھ نشریات جاری ہیں۔',
      'bc.chunkOffline': 'سرور سے رابطہ منقطع ہو گیا، حصے خود بخود دوبارہ بھیجے جائیں گے…',
      'bc.slowNetwork': 'نیٹ ورک سست ہے، ایک پرانا حصہ چھوڑ دیا گیا۔',
      'bc.sessionEnded': 'نشریاتی سیشن ختم ہو گیا۔',
      'bc.sessionMoved': 'نشریات کسی دوسرے آلے پر منتقل ہو گئیں یا سیشن ختم ہو گیا۔',
      'bc.uploadFailed': 'خطبہ اپلوڈ نہیں ہو سکا۔',
      'bc.uploadDropped': 'فائل اپلوڈ کرتے وقت رابطہ منقطع ہو گیا۔',
      'bc.transcribing': 'آواز کو متن میں تبدیل کیا جا رہا ہے…',
      'bc.translating': 'ترجمہ اور اشاعت: {total} میں سے {n}',
      'bc.processed': 'کارروائی مکمل: {n} حصے نمازیوں تک پہنچ گئے۔',
      'bc.processedHint': 'نمازیوں کے پڑھ لینے کے بعد آپ نشریات روک سکتے ہیں۔',
      'bc.ended': 'نشریات ختم ہو گئیں، جزاک اللہ خیراً۔',
      'bc.duration': 'نشریات کا دورانیہ',
      'bc.peak': 'زیادہ سے زیادہ سامعین',
      'bc.verses': 'تصدیق شدہ آیات',
      'bc.unclearSegments': 'غیر واضح حصے',
      'bc.newBroadcast': 'نئی نشریات',
      'bc.viewTranscript': 'خطبے کا متن دیکھیں',

      'privacy.title': 'رازداری اور ڈیٹا کا تحفظ',
      'privacy.subtitle': 'Privacy Policy',
      'privacy.noDataTitle': 'ہم نمازیوں کا ڈیٹا جمع نہیں کرتے',
      'privacy.noData1': 'ہم نام، فون نمبر یا ای میل نہیں مانگتے، اور نمازیوں کا کوئی ڈیٹا بیس نہیں ہے۔',
      'privacy.noData2': 'سامعین کی تعداد صرف سرور کی میموری میں لمحہ بہ لمحہ گنی جاتی ہے، کسی ذاتی شناخت کے بغیر۔',
      'privacy.noData3': 'انٹرفیس کی زبان صرف اسی آلے کے براؤزر میں محفوظ ہوتی ہے، اور خطبے کے ترجمے کی زبان صرف موجودہ سیشن کے لیے۔ ان میں سے کوئی بھی سرور پر محفوظ نہیں ہوتی۔',
      'privacy.noAudioTitle': 'ہم نمازیوں کی آواز ریکارڈ نہیں کرتے',
      'privacy.noAudio1': 'نمازی کا آلہ کوئی آواز نہیں بھیجتا؛ وہ صرف متن وصول کرتا ہے۔',
      'privacy.noAccountTitle': 'اکاؤنٹ کی ضرورت نہیں',
      'privacy.noAccount1': 'لنک کھولیں اور اپنی زبان منتخب کریں، نہ رجسٹریشن نہ پاس ورڈ۔',
      'privacy.khateebTitle': 'خطیب کی آواز ترجمے کے لیے پروسیس ہوتی ہے، محفوظ نہیں کی جاتی',
      'privacy.khateeb1': 'ہر آڈیو حصہ تقریر سے متن کی سروس (OpenAI) کو بھیجا جاتا ہے، اور کارروائی ختم ہوتے ہی عارضی فائل حذف کر دی جاتی ہے۔',
      'privacy.khateeb2': 'خطبے کا متن اور ترجمہ دوبارہ پڑھنے کے لیے عارضی طور پر سرور کی میموری میں رہتے ہیں، اور نشریات ختم ہونے کے دو گھنٹے بعد خود بخود حذف ہو جاتے ہیں۔',
      'privacy.khateeb3': 'قرآنی آیات QuranEnc کے تصدیق شدہ تراجم کے ساتھ دکھائی جاتی ہیں؛ باقی کلام کا خودکار ترجمہ ہے جس میں غلطیاں ہو سکتی ہیں، اور اصل حوالہ خطیب کا کلام ہے۔',

      'err.offline': 'منبر سرور تک رسائی نہیں ہو سکی۔ صفحہ سرور ہی سے کھولیں (مثلاً http://127.0.0.1:8000/broadcast)، یا لنک میں ‎?api=http://127.0.0.1:8765 شامل کریں۔',
      'err.generic': 'کچھ غلط ہو گیا۔ دوبارہ کوشش کریں۔',
      'err.invalid_code': 'کوڈ درست نہیں۔',
      'err.missing_code': 'نشریاتی کوڈ درج کریں۔',
      'err.unknown_mosque': 'مسجد نہیں ملی۔',
      'err.unknown_room': 'مسجد نہیں ملی۔',
      'err.codes_not_configured': 'اس مسجد کے لیے نشریاتی کوڈ ترتیب نہیں دیا گیا۔',
      'err.already_live': 'اس مسجد میں نشریات پہلے سے جاری ہیں۔',
      'err.already_ended': 'نشریات پہلے ہی ختم ہو چکی ہیں۔',
      'err.not_live': 'نشریات جاری نہیں ہیں۔',
      'err.unauthorized': 'یہ نشریاتی سیشن مجاز نہیں۔',
      'err.processing': 'اس مسجد میں ایک ریکارڈ شدہ خطبے پر کارروائی جاری ہے۔',
      'err.empty_audio': 'آڈیو حصہ خالی ہے۔',
      'err.unsupported_audio': 'فائل کی یہ قسم معاون نہیں۔ معاون اقسام: MP3, M4A, WAV, WEBM, OGG, MP4, FLAC۔',
      'err.file_too_large': 'فائل کا سائز حد سے زیادہ ہے۔',
      'err.audio_processing_failed': 'آواز پر کارروائی عارضی طور پر ممکن نہیں۔ اگلے حصے کے ساتھ کوشش جاری رہے گی۔',
      'err.ai_unavailable': 'سرور پر تقریر کی شناخت کی سروس ترتیب نہیں دی گئی۔ ‎.env فائل میں OPENAI_API_KEY شامل کریں، پھر سرور دوبارہ شروع کریں۔',
      'err.ai_key_invalid': 'سرور پر OpenAI کی کلید غلط ہے یا اسے اجازت نہیں۔ OPENAI_API_KEY اپڈیٹ کریں، پھر سرور دوبارہ شروع کریں۔',
      'err.translation_failed': 'خودکار ترجمہ عارضی طور پر دستیاب نہیں۔',
      'err.unsupported_language': 'زبان معاون نہیں۔',
      'err.unclear_text': 'متن میں واضح عربی کلام موجود نہیں۔',
      'err.no_arabic_speech': 'فائل میں واضح عربی کلام نہیں پہچانا گیا۔',
      'err.recorded_failed': 'ریکارڈ شدہ خطبے پر کارروائی نہیں ہو سکی۔',
      'err.server_error': 'سرور میں ایک غیر متوقع خرابی پیش آئی۔',
    },

    hi: {
      'ui.language': 'इंटरफ़ेस की भाषा',
      'common.back': 'वापस',
      'common.privacy': 'गोपनीयता नीति',
      'common.mb': 'MB',

      'title.home': 'मिंबर — जुमे का ख़ुतबा अपनी भाषा में समझें',
      'title.listen': 'मिंबर — नमाज़ी',
      'title.broadcast': 'मिंबर — प्रसारण',
      'title.privacy': 'मिंबर — गोपनीयता',

      'home.headline': 'जुमे का ख़ुतबा अपनी भाषा में समझें',
      'home.desc': 'मिंबर आपको जुमे का ख़ुतबा कई भाषाओं में अनुवाद के साथ सुनने देता है, ताकि आप जुमे के मूल्यों और अर्थों से जुड़ सकें।',
      'home.worshipper': 'मैं नमाज़ी हूँ',
      'home.supervisor': 'मस्जिद पर्यवेक्षक लॉग इन',

      'listen.start': 'शुरू करें',
      'listen.chooseTitle': 'अपनी भाषा चुनें',
      'listen.chooseSub': 'ख़ुतबे के अनुवाद की भाषा',
      'listen.arabicNote': '(ख़ुतबे का पाठ)',
      'listen.arabicSub': 'कम सुनने वालों के लिए',
      'listen.continue': 'जारी रखें',
      'listen.sessionNote': 'इस सत्र के दौरान आपको दोबारा भाषा नहीं चुननी होगी।',
      'listen.sermonLanguage': 'ख़ुतबे के अनुवाद की भाषा',
      'listen.waiting': 'ख़ुतबा अभी शुरू नहीं हुआ है।',
      'listen.waitingSub': 'यह पेज खुला रखें, अनुवाद अपने आप दिखाई देगा।',
      'listen.connected': 'जुड़ा हुआ',
      'listen.connecting': 'जुड़ रहा है…',
      'listen.disconnected': 'कनेक्शन टूट गया',
      'listen.live': 'लाइव',
      'listen.disc': 'कनेक्शन टूट गया, दोबारा जोड़ा जा रहा है।',
      'listen.discSub': 'आपसे कुछ नहीं छूटेगा।',
      'listen.disclaimerTranslation': 'AI द्वारा स्वचालित अनुवाद, मूल संदर्भ ख़तीब के शब्द हैं।',
      'listen.disclaimerTranscript': 'ख़तीब के शब्दों का स्वचालित पाठ, इसमें ग़लतियाँ हो सकती हैं।',
      'listen.feedTitle': 'ख़ुतबे का रिकॉर्ड',
      'listen.now': 'अभी',
      'listen.quran': 'क़ुरआन',
      'listen.hadith': 'हदीस, जैसा ख़तीब ने बताया',
      'listen.unclear': 'अस्पष्ट',
      'listen.unclearText': 'ख़ुतबे का यह हिस्सा साफ़ पहचाना नहीं जा सका।',
      'listen.sura': 'सूरह',
      'listen.quranSource': 'क़ुरआन का पाठ: किंग फ़हद क़ुरआन प्रिंटिंग कॉम्प्लेक्स',
      'listen.translationOf': 'पवित्र क़ुरआन के अर्थों का अनुवाद',
      'listen.failNote': 'इस हिस्से का स्वचालित अनुवाद उपलब्ध नहीं, अरबी पाठ दिखाया जा रहा है।',
      'listen.latest': 'नवीनतम',
      'listen.fontUp': 'बड़ा पाठ',
      'listen.fontDown': 'छोटा पाठ',
      'listen.ended': 'ख़ुतबा समाप्त हो गया।',
      'listen.dua': 'अल्लाह हमसे और आपसे क़बूल फ़रमाए।',
      'listen.rating': 'अनुवाद कितना स्पष्ट था?',
      'listen.thanks': 'धन्यवाद।',
      'listen.replay': 'ख़ुतबा दोबारा पढ़ें',
      'listen.replayEmpty': 'ख़ुतबे की कोई अस्थायी प्रति उपलब्ध नहीं है।',
      'listen.replayFailed': 'ख़ुतबा लोड नहीं हो सका।',
      'listen.unknownRoom': 'मस्जिद का यह लिंक मान्य नहीं है।',

      'bc.title': 'प्रसारण पेज',
      'bc.sub': 'मुअज़्ज़िन या मस्जिद पर्यवेक्षक के लिए।',
      'bc.mosque': 'मस्जिद चुनें',
      'bc.code': 'प्रसारण कोड',
      'bc.showCode': 'कोड दिखाएँ',
      'bc.login': 'लॉग इन',
      'bc.khateeb': 'ख़तीब',
      'bc.khateebNone': 'निर्धारित नहीं',
      'bc.khateebHint': 'ख़तीब को डिवाइस छूने की ज़रूरत नहीं है।',
      'bc.enterCode': 'प्रसारण कोड दर्ज करें।',
      'bc.verifyFailed': 'कोड की पुष्टि नहीं हो सकी।',
      'bc.ready': 'प्रसारण के लिए तैयार',
      'bc.mic': 'माइक्रोफ़ोन',
      'bc.file': 'ऑडियो फ़ाइल',
      'bc.micPreparing': 'माइक्रोफ़ोन तैयार हो रहा है…',
      'bc.micSpeak': 'माइक्रोफ़ोन जाँचने के लिए डिवाइस के पास बोलें',
      'bc.micWorks': 'माइक्रोफ़ोन काम कर रहा है',
      'bc.micNotFound': 'इस डिवाइस पर कोई माइक्रोफ़ोन नहीं मिला।',
      'bc.micFailed': 'माइक्रोफ़ोन शुरू नहीं हो सका।',
      'bc.fileHint': 'रिकॉर्ड किया गया ख़ुतबा, अधिकतम {max} MB (MP3, M4A, WAV, OGG, WEBM)।',
      'bc.fileInfo': '{name} — {size} MB',
      'bc.fileTooBigInfo': 'फ़ाइल {size} MB की है, जो {max} MB की सीमा से अधिक है।',
      'bc.waiting': 'ख़ुतबे का इंतज़ार कर रहे नमाज़ी',
      'bc.worshippers': 'नमाज़ी',
      'bc.tip': 'डिवाइस ख़तीब के पास रखें और स्क्रीन बंद न करें।',
      'bc.start': 'प्रसारण शुरू करें',
      'bc.logout': 'लॉग आउट',
      'bc.alreadyLiveHint': 'इस मस्जिद में प्रसारण पहले से चल रहा है। इस डिवाइस से जारी रखने के लिए “प्रसारण शुरू करें” दबाएँ।',
      'bc.speechOff': 'ऑडियो प्रसारण शुरू नहीं हो सकता: सर्वर पर वाक् पहचान सेवा कॉन्फ़िगर नहीं है। .env फ़ाइल में OPENAI_API_KEY जोड़ें, फिर सर्वर दोबारा शुरू करें।',
      'bc.chooseFile': 'पहले एक ऑडियो फ़ाइल चुनें।',
      'bc.fileTooBig': 'फ़ाइल आकार सीमा से अधिक है।',
      'bc.confirmResume': 'इस मस्जिद में प्रसारण पहले से चल रहा है। क्या इस डिवाइस से जारी रखें?',
      'bc.startFailed': 'प्रसारण शुरू नहीं हो सका।',
      'bc.deniedTitle': 'माइक्रोफ़ोन की अनुमति चाहिए',
      'bc.insecureTitle': 'माइक्रोफ़ोन के लिए सुरक्षित कनेक्शन ज़रूरी है',
      'bc.step1': 'iPhone या iPad में “Settings” खोलें, फिर “Safari” चुनें।',
      'bc.step2': 'वेबसाइट सेटिंग्स में “Microphone” चुनें।',
      'bc.step3': '“Allow” चुनें, फिर इस पेज पर लौटकर “फिर से कोशिश करें” दबाएँ।',
      'bc.insecureHint': 'माइक्रोफ़ोन तभी काम करता है जब मिंबर https:// से शुरू होने वाले सुरक्षित लिंक से खोला जाए।',
      'bc.retry': 'फिर से कोशिश करें',
      'bc.uploadInstead': 'रिकॉर्ड किया गया ख़ुतबा अपलोड करें',
      'bc.liveNow': 'अभी प्रसारण',
      'bc.recorded': 'रिकॉर्ड किया गया ख़ुतबा',
      'bc.uploading': 'फ़ाइल अपलोड हो रही है…',
      'bc.uploadOther': 'दूसरी फ़ाइल अपलोड करें',
      'bc.detected': 'पहचाना गया अरबी पाठ',
      'bc.waitingFirst': 'पहले हिस्से का इंतज़ार…',
      'bc.unclearMarker': '— अस्पष्ट —',
      'bc.listeners': 'श्रोता',
      'bc.listenerUnit': 'श्रोता',
      'bc.stop': 'प्रसारण रोकें',
      'bc.confirmStop': 'क्या प्रसारण रोक दें?',
      'bc.stopping': 'आख़िरी हिस्सा भेजा जा रहा है और प्रसारण रोका जा रहा है…',
      'bc.stopFailed': 'प्रसारण रोका नहीं जा सका।',
      'bc.stopOffline': 'प्रसारण रोकने के लिए सर्वर से संपर्क नहीं हो सका। फिर से कोशिश करें।',
      'bc.lastChunk': 'आख़िरी हिस्सा {n} सेकंड पहले',
      'bc.chunkUnclear': 'अस्पष्ट हिस्सा, प्रसारण जारी है।',
      'bc.chunkRetry': 'हिस्से को प्रोसेस नहीं किया जा सका, फिर से कोशिश हो रही है…',
      'bc.chunkSkipped': 'हिस्से को प्रोसेस नहीं किया जा सका, अगले हिस्से के साथ प्रसारण जारी है।',
      'bc.chunkOffline': 'सर्वर से कनेक्शन टूट गया, हिस्से अपने आप दोबारा भेजे जाएँगे…',
      'bc.slowNetwork': 'नेटवर्क धीमा है, एक पुराना हिस्सा छोड़ दिया गया।',
      'bc.sessionEnded': 'प्रसारण सत्र समाप्त हो गया।',
      'bc.sessionMoved': 'प्रसारण किसी दूसरे डिवाइस पर चला गया या सत्र समाप्त हो गया।',
      'bc.uploadFailed': 'ख़ुतबा अपलोड नहीं हो सका।',
      'bc.uploadDropped': 'फ़ाइल अपलोड करते समय कनेक्शन टूट गया।',
      'bc.transcribing': 'आवाज़ को पाठ में बदला जा रहा है…',
      'bc.translating': 'अनुवाद और प्रकाशन: {total} में से {n}',
      'bc.processed': 'प्रोसेसिंग पूरी: {n} हिस्से नमाज़ियों तक पहुँचे।',
      'bc.processedHint': 'नमाज़ियों के पढ़ लेने के बाद आप प्रसारण रोक सकते हैं।',
      'bc.ended': 'प्रसारण समाप्त हुआ, अल्लाह आपको अच्छा बदला दे।',
      'bc.duration': 'प्रसारण की अवधि',
      'bc.peak': 'अधिकतम श्रोता',
      'bc.verses': 'प्रमाणित आयतें',
      'bc.unclearSegments': 'अस्पष्ट हिस्से',
      'bc.newBroadcast': 'नया प्रसारण',
      'bc.viewTranscript': 'ख़ुतबे का पाठ देखें',

      'privacy.title': 'गोपनीयता और डेटा सुरक्षा',
      'privacy.subtitle': 'Privacy Policy',
      'privacy.noDataTitle': 'हम नमाज़ियों का डेटा जमा नहीं करते',
      'privacy.noData1': 'हम नाम, फ़ोन नंबर या ईमेल नहीं माँगते, और नमाज़ियों का कोई डेटाबेस नहीं है।',
      'privacy.noData2': 'श्रोताओं की संख्या केवल सर्वर की मेमोरी में लाइव गिनी जाती है, किसी व्यक्तिगत पहचान के बिना।',
      'privacy.noData3': 'इंटरफ़ेस की भाषा केवल इसी डिवाइस के ब्राउज़र में सहेजी जाती है, और ख़ुतबे के अनुवाद की भाषा केवल मौजूदा सत्र के लिए। इनमें से कोई भी सर्वर पर संग्रहीत नहीं होती।',
      'privacy.noAudioTitle': 'हम नमाज़ियों की आवाज़ रिकॉर्ड नहीं करते',
      'privacy.noAudio1': 'नमाज़ी का डिवाइस कोई आवाज़ नहीं भेजता; वह केवल पाठ प्राप्त करता है।',
      'privacy.noAccountTitle': 'खाते की ज़रूरत नहीं',
      'privacy.noAccount1': 'लिंक खोलें और अपनी भाषा चुनें — न पंजीकरण, न पासवर्ड।',
      'privacy.khateebTitle': 'ख़तीब की आवाज़ अनुवाद के लिए प्रोसेस होती है, सहेजी नहीं जाती',
      'privacy.khateeb1': 'हर ऑडियो हिस्सा वाक्-से-पाठ सेवा (OpenAI) को भेजा जाता है, और प्रोसेसिंग ख़त्म होते ही अस्थायी फ़ाइल हटा दी जाती है।',
      'privacy.khateeb2': 'ख़ुतबे का पाठ और अनुवाद दोबारा पढ़ने के लिए अस्थायी रूप से सर्वर की मेमोरी में रहते हैं, और प्रसारण ख़त्म होने के दो घंटे बाद अपने आप हट जाते हैं।',
      'privacy.khateeb3': 'क़ुरआन की आयतें QuranEnc के प्रमाणित अनुवादों के साथ दिखाई जाती हैं; बाक़ी स्वचालित अनुवाद है जिसमें ग़लतियाँ हो सकती हैं, और मूल संदर्भ ख़तीब के शब्द हैं।',

      'err.offline': 'मिंबर सर्वर तक नहीं पहुँचा जा सका। पेज सर्वर से ही खोलें (जैसे http://127.0.0.1:8000/broadcast), या लिंक में ?api=http://127.0.0.1:8765 जोड़ें।',
      'err.generic': 'कुछ ग़लत हो गया। फिर से कोशिश करें।',
      'err.invalid_code': 'कोड ग़लत है।',
      'err.missing_code': 'प्रसारण कोड दर्ज करें।',
      'err.unknown_mosque': 'मस्जिद नहीं मिली।',
      'err.unknown_room': 'मस्जिद नहीं मिली।',
      'err.codes_not_configured': 'इस मस्जिद के लिए कोई प्रसारण कोड कॉन्फ़िगर नहीं है।',
      'err.already_live': 'इस मस्जिद में प्रसारण पहले से चल रहा है।',
      'err.already_ended': 'प्रसारण पहले ही समाप्त हो चुका है।',
      'err.not_live': 'प्रसारण चालू नहीं है।',
      'err.unauthorized': 'यह प्रसारण सत्र अधिकृत नहीं है।',
      'err.processing': 'इस मस्जिद में एक रिकॉर्ड किए गए ख़ुतबे की प्रोसेसिंग चल रही है।',
      'err.empty_audio': 'ऑडियो हिस्सा ख़ाली है।',
      'err.unsupported_audio': 'यह फ़ाइल प्रारूप समर्थित नहीं है। समर्थित: MP3, M4A, WAV, WEBM, OGG, MP4, FLAC।',
      'err.file_too_large': 'फ़ाइल आकार सीमा से अधिक है।',
      'err.audio_processing_failed': 'ऑडियो प्रोसेसिंग अस्थायी रूप से उपलब्ध नहीं है। अगले हिस्से के साथ कोशिश जारी रहेगी।',
      'err.ai_unavailable': 'सर्वर पर वाक् पहचान सेवा कॉन्फ़िगर नहीं है। .env फ़ाइल में OPENAI_API_KEY जोड़ें, फिर सर्वर दोबारा शुरू करें।',
      'err.ai_key_invalid': 'सर्वर पर OpenAI कुंजी अमान्य है या उसके पास अनुमति नहीं है। OPENAI_API_KEY अपडेट करें, फिर सर्वर दोबारा शुरू करें।',
      'err.translation_failed': 'स्वचालित अनुवाद अस्थायी रूप से उपलब्ध नहीं है।',
      'err.unsupported_language': 'भाषा समर्थित नहीं है।',
      'err.unclear_text': 'पाठ में स्पष्ट अरबी वाणी नहीं है।',
      'err.no_arabic_speech': 'फ़ाइल में स्पष्ट अरबी वाणी नहीं पहचानी गई।',
      'err.recorded_failed': 'रिकॉर्ड किए गए ख़ुतबे को प्रोसेस नहीं किया जा सका।',
      'err.server_error': 'सर्वर में एक अप्रत्याशित त्रुटि हुई।',
    },
  };

  function read() {
    try { return localStorage.getItem(KEY); } catch { return null; }
  }
  function write(value) {
    try { localStorage.setItem(KEY, value); } catch {}
  }

  let lang = LANGS[read()] ? read() : 'ar';

  function t(key, vars) {
    let s = (M[lang] && M[lang][key]) ?? M.ar[key] ?? key;
    if (vars) s = s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? vars[k] : m));
    return s;
  }

  function has(key) {
    return key in M.ar;
  }

  function error(code, fallback) {
    return code && has('err.' + code) ? t('err.' + code) : (fallback || t('err.generic'));
  }

  const SVG = 'http://www.w3.org/2000/svg';
  function svgUse(cls, href) {
    const svg = document.createElementNS(SVG, 'svg');
    svg.setAttribute('class', cls);
    svg.setAttribute('aria-hidden', 'true');
    const use = document.createElementNS(SVG, 'use');
    use.setAttribute('href', 'assets/icons.svg#' + href);
    svg.append(use);
    return svg;
  }

  function apply(root = document) {
    const L = LANGS[lang];
    document.documentElement.lang = lang;
    document.documentElement.dir = L.dir;
    root.querySelectorAll('[data-i18n]').forEach(n => { n.textContent = t(n.dataset.i18n); });
    root.querySelectorAll('[data-i18n-placeholder]').forEach(n => { n.placeholder = t(n.dataset.i18nPlaceholder); });
    root.querySelectorAll('[data-i18n-aria-label]').forEach(n => { n.setAttribute('aria-label', t(n.dataset.i18nAriaLabel)); });
    const titleKey = document.documentElement.dataset.i18nTitle;
    if (titleKey) document.title = t(titleKey);
    renderSwitchers();
  }

  function renderSwitchers() {
    document.querySelectorAll('[data-ui-lang]').forEach(box => {
      const L = LANGS[lang];
      const button = box.querySelector('.lang-pill');
      button.replaceChildren(svgUse('i chev', 'chevron-down'), document.createTextNode(' '), Object.assign(document.createElement('span'), {textContent: L.name, lang, dir: L.dir}), document.createTextNode(' '), svgUse('i', 'globe'));
      button.setAttribute('aria-label', t('ui.language') + ': ' + L.name);
      box.querySelectorAll('[role=option]').forEach(o => o.setAttribute('aria-selected', String(o.dataset.lang === lang)));
    });
  }

  function mountSwitchers() {
    document.querySelectorAll('[data-ui-lang]').forEach(box => {
      if (box.dataset.mounted) return;
      box.dataset.mounted = '1';
      box.classList.add('ui-lang');
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'lang-pill';
      button.setAttribute('aria-haspopup', 'listbox');
      button.setAttribute('aria-expanded', 'false');
      const menu = document.createElement('ul');
      menu.className = 'ui-lang-menu';
      menu.setAttribute('role', 'listbox');
      menu.hidden = true;
      ORDER.forEach(code => {
        const L = LANGS[code];
        const li = document.createElement('li');
        const opt = document.createElement('button');
        opt.type = 'button';
        opt.setAttribute('role', 'option');
        opt.dataset.lang = code;
        opt.lang = code;
        opt.dir = L.dir;
        opt.append(svgUse('flag', L.flag), Object.assign(document.createElement('span'), {textContent: L.name}), svgUse('i check', 'check'));
        opt.addEventListener('click', () => { close(); set(code); });
        li.append(opt);
        menu.append(li);
      });
      const close = () => { menu.hidden = true; button.setAttribute('aria-expanded', 'false'); };
      button.addEventListener('click', e => {
        e.stopPropagation();
        const open = menu.hidden;
        document.querySelectorAll('.ui-lang-menu').forEach(m => { m.hidden = true; });
        menu.hidden = !open;
        button.setAttribute('aria-expanded', String(open));
        if (open) (menu.querySelector('[aria-selected=true]') || menu.querySelector('button')).focus();
      });
      menu.addEventListener('keydown', e => {
        const items = [...menu.querySelectorAll('button')];
        const i = items.indexOf(document.activeElement);
        if (e.key === 'ArrowDown') { e.preventDefault(); items[(i + 1) % items.length].focus(); }
        if (e.key === 'ArrowUp') { e.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
        if (e.key === 'Escape') { close(); button.focus(); }
      });
      document.addEventListener('click', e => { if (!box.contains(e.target)) close(); });
      box.append(button, menu);
    });
  }

  function set(code) {
    if (!LANGS[code] || code === lang) return;
    lang = code;
    write(code);
    apply();
    window.dispatchEvent(new CustomEvent('minbar:lang', {detail: code}));
  }

  // Set direction before first paint to avoid a layout flash.
  document.documentElement.lang = lang;
  document.documentElement.dir = LANGS[lang].dir;
  document.addEventListener('DOMContentLoaded', () => { mountSwitchers(); apply(); });

  window.I18N = {
    LANGS,
    get lang() { return lang; },
    get dir() { return LANGS[lang].dir; },
    get locale() { return LANGS[lang].locale; },
    t, error, apply, set,
  };
})();
