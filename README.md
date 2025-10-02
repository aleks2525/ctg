# КТГ Анализатор ИТЭЛМА

Программный комплекс для анализа кардиотокограммы (КТГ) с использованием эвристических модулей и ИИ.

##  Возможности

- **Анализ исторических данных КТГ** - загрузка и анализ ранее записанных КТГ
- **Мониторинг в реальном времени** - просмотр данных КТГ в режиме реального времени
- **База данных пациенток** - управление данными пациенток
- **Эвристический анализ**:
  - Классификация по FIGO/NICE
  - Классификация по NICHD/ACOG
  - Учет факторов риска анамнеза
- **ИИ модуль** - прогнозирование на 15, 30 и 60+ минут
- **Расчет метрик**:
  - Базовый ритм (baseline FHR)
  - Вариабельность
  - Акселерации и децелерации
  - Риск гипоксии
- **Генерация отчетов** - автоматическое формирование отчетов в HTML

## 📋 Требования

- Python 3.8+
- pip

## 🔧 Установка

1. Клонируйте репозиторий или перейдите в папку проекта:
```bash
cd "D:\Moscow\ITELMA\New"
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте необходимые папки:
```bash
mkdir -p data/uploads
```

## ▶️ Запуск

Запустите сервер FastAPI:

```bash
python app.py
```

Сервер будет доступен по адресу: **http://localhost:8000**

## 📁 Структура проекта

```
.
├── app.py                      # Главный файл приложения
├── requirements.txt            # Зависимости Python
├── README.md                   # Документация
│
├── api/                        # API endpoints
│   ├── __init__.py
│   ├── schemas.py             # Pydantic схемы
│   ├── patients.py            # CRUD операции с пациентками
│   ├── sessions.py            # Управление сессиями КТГ
│   ├── analysis.py            # Анализ КТГ данных
│   └── reports.py             # Генерация отчетов
│
├── database/                   # База данных
│   ├── __init__.py
│   └── models.py              # SQLAlchemy модели
│
├── services/                   # Бизнес-логика
│   ├── __init__.py
│   ├── database_service.py    # Сервис работы с БД
│   ├── file_service.py        # Сервис работы с файлами
│   ├── analysis_service.py    # Сервис анализа КТГ
│   └── report_service.py      # Сервис генерации отчетов
│
├── ctg_analysis/               # Модули анализа КТГ
│   ├── __init__.py
│   ├── common.py              # Общие функции
│   ├── figo_nice.py           # Классификация FIGO/NICE
│   ├── nichd_acog.py          # Классификация NICHD/ACOG
│   ├── variability.py         # Оценка вариабельности
│   ├── hypoxia.py             # Расчет риска гипоксии
│   ├── ai_module.py           # ИИ модуль
│   └── risk_adjustment.py     # Учет факторов риска
│
├── static/                     # Статические файлы
│   ├── index.html             # Главная страница
│   ├── styles.css             # Стили
│   └── logo.png               # Логотип
│
└── data/                       # Данные
    └── uploads/               # Загруженные файлы КТГ
```

## 📊 Формат данных

CSV файлы должны содержать два столбца:
```csv
time_sec,value
0,120
1,122
2,121
...
```

- **FHR файл**: ЧСС плода (уд/мин)
- **UC файл**: Сокращения матки (мм рт. ст.)

## 🔬 Модули анализа

### FIGO/NICE
Классификация на основе международных рекомендаций FIGO/NICE:
- **Normal** - нормальная КТГ
- **Suspicious** - подозрительная КТГ
- **Pathological** - патологическая КТГ

### NICHD/ACOG
Классификация на основе рекомендаций NICHD/ACOG:
- **Category I** - нормальная КТГ
- **Category II** - неопределенная КТГ
- **Category III** - патологическая КТГ

### Факторы риска
Учитываются следующие факторы анамнеза:
- Сахарный диабет (вес: 2)
- Анемия (вес: 1)
- Хроническая гипертония (вес: 2)
- Преэклампсия (вес: 3)
- Инфекционные заболевания (вес: 2)
- Многоплодная беременность (вес: 2)
- Патологии плаценты и пуповины (вес: 3)
- Нарушение срока беременности (вес: 2)

При балле риска ≥ 4 классификация повышается на одну категорию.

## 🌐 API Endpoints

### Пациентки
- `POST /api/patients/` - создать пациентку
- `GET /api/patients/` - получить список пациенток
- `GET /api/patients/{id}` - получить пациентку по ID
- `PUT /api/patients/{id}` - обновить данные пациентки
- `DELETE /api/patients/{id}` - удалить пациентку
- `GET /api/patients/search/{query}` - поиск пациенток

### Сессии КТГ
- `POST /api/sessions/` - создать сессию
- `GET /api/sessions/patient/{patient_id}` - получить сессии пациентки
- `GET /api/sessions/{id}` - получить сессию по ID
- `POST /api/sessions/{id}/upload-fhr` - загрузить FHR файл
- `POST /api/sessions/{id}/upload-uc` - загрузить UC файл
- `GET /api/sessions/{id}/data` - получить данные для графиков
- `DELETE /api/sessions/{id}` - удалить сессию

### Анализ
- `POST /api/analysis/{session_id}/analyze` - выполнить анализ КТГ
- `GET /api/analysis/{session_id}/statistics` - получить статистику

### Отчеты
- `POST /api/reports/` - создать отчет
- `GET /api/reports/session/{session_id}` - получить отчет по сессии
- `GET /api/reports/patient/{patient_id}` - получить отчеты пациентки
- `GET /api/reports/{id}/download` - скачать отчет в HTML

## 📝 Пример использования API

### Создание пациентки и анализ КТГ

```python
import requests

# 1. Создать пациентку
patient_data = {
    "full_name": "Иванова Анна Петровна",
    "diagnosis": "Беременность 38 недель",
    "diabetes": False,
    "preeclampsia": True,
    "term": False
}
response = requests.post("http://localhost:8000/api/patients/", json=patient_data)
patient = response.json()

# 2. Создать сессию
session_data = {"patient_id": patient["id"]}
response = requests.post("http://localhost:8000/api/sessions/", json=session_data)
session = response.json()

# 3. Загрузить FHR файл
with open("fhr_data.csv", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"http://localhost:8000/api/sessions/{session['id']}/upload-fhr",
        files=files
    )

# 4. Загрузить UC файл
with open("uc_data.csv", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"http://localhost:8000/api/sessions/{session['id']}/upload-uc",
        files=files
    )

# 5. Выполнить анализ
analysis_params = {
    "figo_nice": True,
    "nichd_acog": True,
    "ai": True
}
response = requests.post(
    f"http://localhost:8000/api/analysis/{session['id']}/analyze",
    json=analysis_params
)
results = response.json()

print(f"Базовый ритм: {results['fhr_base']} уд/мин")
print(f"Статус: {results['status']}")
print(f"FIGO/NICE: {results['figo_result']['label']}")
print(f"NICHD/ACOG: {results['nichd_result']['label']}")
```

## Отладка

Логи сервера будут выводиться в консоль. Для более детальной отладки используйте:

```bash
uvicorn app:app --reload --log-level debug
```

## 📄 Лицензия

© 2025 ITELMA. Все права защищены.

## 👥 Авторы

Разработано для ITELMA

