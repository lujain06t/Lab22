# دليل المختبر بالعربي: من الملفات إلى تشغيل الخدمة

هذا المشروع مبني على موديل churn الموجود في Lab 1 Starter Kit. `churn` تعني ترك العميل للخدمة. الموديل يتعلم من خمسة أعمدة: ثلاثة أرقام (`tenure_months`, `monthly_charges`, `support_calls`) وعمودين نصيين (`contract`, `internet_service`). لا يحتاج المشروع تنزيل موديل جاهز من الإنترنت؛ ملف `model.joblib` يُنتج عند تدريب الكود.

## 1) جهّز البرامج والحسابات

- نزّل Python 3.11 وثبّته، واختر إضافة Python إلى PATH إن ظهرت.
- نزّل Visual Studio Code لفتح ملفات المشروع.
- نزّل Git for Windows أو GitHub Desktop لرفع المشروع إلى GitHub.
- نزّل Docker Desktop، وافتحه وانتظر أن يصبح جاهزًا. إذا سأل عن المحرك، اختر WSL 2.
- أنشئ حساب GitHub مجانيًا. استخدم حساب الجامعة الموجود عندك في e-learning وTeams للتسليم؛ لا تضع كلمة مرورك أو رقمك الجامعي في مستودع GitHub.
- لا تحتاج Docker Hub ولا مفتاح API. سير العمل ينشر الصورة إلى GHCR بواسطة رمز GitHub المؤقت.

## 2) افتح المشروع

افتح مجلد `AI381-Lab2-Churn-Service` في VS Code من File > Open Folder. افتح Terminal داخل VS Code، وتأكد أن المسار هو مجلد المشروع نفسه، أي المجلد الذي بداخله `requirements.txt` و`Dockerfile`.

إذا أردت العمل على نسخة Starter Kit الأصلية بدل هذا المجلد، انسخ إليها ملفات هذا المشروع. احتفظ بملفي البيانات `data/churn_v1.csv` و`data/churn_v2.csv` ولا تحذفهما.

## 3) أنشئ بيئة Python وثبّت المكتبات

نفّذ الأوامر التالية في PowerShell، سطرًا سطرًا:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

البيئة الافتراضية `.venv` مساحة خاصة بمكتبات هذا المشروع، حتى لا تختلط بمشاريعك الأخرى. إذا رفض PowerShell أمر التفعيل بسبب سياسة تشغيل السكربت، لا تغيّر إعدادات الجهاز؛ نفّذ Python من المسار المباشر بدل التفعيل:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

إذا لم يعمل التفعيل، استخدم المسار الكامل للمفسّر في كل أمر بدل كلمة `python`، هكذا: `.\.venv\Scripts\python.exe`.

## 4) درّب الموديل وأنشئ ملفه

```powershell
python -m src.train.train
```

سيقرأ البرنامج `data/churn_v1.csv`، يقسم البيانات إلى تدريب وفحص، ويدرّب نفس خط أنابيب الـnotebook: توحيد الأرقام، تحويل الفئات النصية إلى أرقام، ثم Logistic Regression. سيطبع F1 وAUC ويحفظ `model.joblib` في مجلد المشروع.

`model.joblib` مستثنى من Git عمدًا؛ GitHub Actions يعيد تدريبه من CSV قبل الاختبارات والبناء. Docker يحتاج الملف عند البناء، لذلك نفّذ التدريب محليًا قبل `docker build`.

للتدريب على النسخة الثانية التي غيّرت اسم `monthly_charges` إلى `monthly_fee`:

```powershell
python -m src.train.train --data data/churn_v2.csv
```

برنامج التدريب يوحّد الاسم داخليًا حتى يبقى طلب الـAPI كما هو.

## 5) شغّل الـAPI وجربها

```powershell
python -m uvicorn src.app.main:app --reload --port 8000
```

اترك هذه النافذة مفتوحة. افتح `http://127.0.0.1:8000/docs` في المتصفح، ثم جرّب `GET /health` وبعدها `POST /predict`. مثال الطلب موجود في `sample_request.json`، والقيم المسموحة للفئات موضحة في README.

أو افتح نافذة PowerShell ثانية ونفّذ:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/health
Invoke-RestMethod -Method Post -Uri http://localhost:8000/predict -ContentType 'application/json' -InFile .\sample_request.json
```

النتيجة `churn_probability` رقم بين صفر وواحد. `predicted_churn` يساوي 1 إذا كان الاحتمال 0.5 أو أكثر، وإلا يساوي 0. هذا تقدير الموديل وليس ضمانًا لما سيحدث للعميل.

## 6) افحص الكود والاختبارات

أوقف خادم API بـCtrl+C ثم نفّذ:

```powershell
python -m ruff check src tests
python -m pytest -q
```

Ruff يبحث عن أخطاء تنسيق/كتابة شائعة. Pytest يشغّل الاختبارات التي كتبتها: تحميل الموديل، صحة `/health`، شكل استجابة `/predict`، رفض المدخل الناقص أو غير المسموح، وحتمية النتيجة عند تكرار نفس الطلب.

## 7) ابنِ Docker وشغّل الحاوية

تأكد أن Docker Desktop يعمل وأن `model.joblib` موجود. ثم:

```powershell
docker build -t ai381-churn .
docker run --rm -p 8000:8000 ai381-churn
```

افتح `http://localhost:8000/docs` أو جرّب `/health` و`/predict` بنفس أوامر PowerShell أعلاه. أوقف الحاوية بـCtrl+C.

Dockerfile فيه مرحلتان: الأولى تثبّت مكتبات التشغيل، والثانية تنسخ ما يلزم فقط. يحدد نسخة أساس Python، ينشئ مستخدمًا محدود الصلاحيات، ويجري فحص صحة دوريًا. هذه هي أسباب multi-stage وpinned image وnon-root وHEALTHCHECK.

## 8) ارفع إلى GitHub وافتح Pull request

الطريقة التالية تبقي `main` نظيفًا وتضع العمل في Pull request:

1. على GitHub أنشئ Repository باسم مثل `ai381-lab2-churn`. اتركه Public إذا كان مناسبًا لك ولتعليمات المساق. فعّل إضافة README عند الإنشاء، ولا ترفع بيانات أو معلومات شخصية.
2. انسخ رابط HTTPS للمستودع، ثم من مجلد أب تختاره نفّذ:

```powershell
git clone https://github.com/USERNAME/ai381-lab2-churn.git
```

استبدل `USERNAME` باسم حسابك. انسخ محتويات مجلد المشروع المجهز إلى المجلد الذي أنشأه `git clone`، ووافق على استبدال README. لا تنسخ مجلد `.git` من أي مكان.
3. افتح Terminal داخل المجلد المستنسخ ونفّذ:

```powershell
git switch -c feature/lab2-container-ci
git add .
git commit -m "Build churn API container and CI"
git push -u origin feature/lab2-container-ci
```

4. افتح صفحة المستودع في GitHub واضغط Compare & pull request. اجعل الوجهة `main`، أنشئ PR، ثم راقب تبويب Checks. يجب أن يعمل lint والاختبارات. أصلح أي فشل، ارفع التعديل على نفس الفرع، وانتظر الفحوصات الخضراء، ثم ادمج PR.
5. بعد الدمج إلى `main`، سير العمل يعيد الفحص، يبني الصورة، يشغّل فحص Trivy، ثم ينشرها إلى `ghcr.io/اسمك/اسم-المستودع` باسم tag يساوي commit SHA. لا تخمّن digest: خذه من سجل خطوة Push image أو صفحة الحزمة.
6. من Settings > Rules/Branches أنشئ قاعدة لـ`main`: اطلب Pull request، واجعل فحص `test` مطلوبًا. قد تحتاج تشغيل PR مرة أولًا حتى يظهر اسم الفحص في قائمة GitHub. جرّب ألا تدمج إلا بعد نجاحه.
7. بعد أول نجاح، ضع شارة CI في README. افتح `README.md` واستبدل `YOUR_GITHUB_USERNAME` و`YOUR_REPOSITORY` باسمك واسم مستودعك الحقيقي.

سير العمل يستخدم `GITHUB_TOKEN` من GitHub Actions للنشر؛ لا تنشئ token شخصيًا ولا تكتبه في الملفات. Actions المستخدمة مثبتة على commit SHA كامل كما تطلب الورقة.

## 9) التسليم والفيديو

سلّم رابط المستودع، رابط/شارة CI، وimage digest الذي أنتجه تشغيلك، والفيديو حسب تعليمات الورقة. سجّل 5–8 دقائق، وأظهر ملف e-learning والاسم والرقم الجامعي حسب المطلوب، ثم وجهك وصوتك. قل اسم كل checkpoint، واشرح الاختبارات وDockerfile ونتائج الـAPI وCI وTrivy وGHCR وحماية `main` وREADME، ثم اختم بما تعطل وما تعلمته. احفظ الملف بالاسم المطلوب في الورقة وارفعه إلى واجب المختبر في Teams مع رابط المستودع.

## أخطاء شائعة

- `model.joblib` مفقود: نفّذ أمر التدريب قبل تشغيل API أو بناء Docker.
- `python` غير معروف: أعد تثبيت Python مع خيار PATH أو استخدم `py -3.11`.
- Docker لا يتصل: افتح Docker Desktop وانتظر حتى يعمل، ثم أعد أمر البناء.
- `/predict` يعيد 422: تأكد من أسماء الحقول وأنواعها والقيم المسموحة في `sample_request.json`.
- فشل Actions أو Trivy: افتح تبويب Actions واقرأ أول خطوة حمراء؛ لا تخفِ فشل الفحص بتغيير إعداداته دون فهم سببه.

