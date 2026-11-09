# Task Scheduling — SPT, EDD, Exact

تطبيق مبسط باستخدام Python وStreamlit لمقارنة خوارزميات جدولة المهام على آلة واحدة.

## الخوارزميات
- **SPT:** ترتيب تصاعدي حسب زمن المعالجة `P`.
- **EDD:** ترتيب تصاعدي حسب موعد التسليم `D`.
- **Exact:** يفحص جميع الترتيبات الممكنة ويختار الأقل في مجموع التأخير الفعلي `ΣTj`، حتى 9 مهام.

## المقاييس
`Cj` زمن الإكمال، `Lj = Cj - Dj` التأخر، `Tj = max(0, Lj)` التأخير الفعلي، `ΣCj` مجموع أزمنة الإكمال، `Lmax` أكبر تأخر، `ΣTj` مجموع التأخير، وعدد المهام المتأخرة.

## فرضيات النموذج
آلة واحدة، كل المهام متاحة عند الزمن صفر، لا يوجد قطع للتنفيذ، ولا توجد أزمنة إعداد.

## المكتبات
- `streamlit`: واجهة التطبيق.
- `pandas`: تنظيم وعرض الجداول.

## التشغيل على Windows
```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## النشر
ارفع كل ملفات هذا المجلد إلى GitHub، ثم اختر `app.py` في خانة Main file path على Streamlit Community Cloud.

## بنية المشروع
```text
single_machine_scheduler_simple/
├── app.py
├── scheduler.py
├── requirements.txt
├── sample_jobs.csv
├── README.md
└── tests/test_scheduler.py
```
