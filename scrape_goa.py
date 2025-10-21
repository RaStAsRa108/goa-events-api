#!/usr/bin/env python3
"""
🏖️ Party Hunt GOA Parser
Парсит только события из Goa
"""
import sys
import requests
import json
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')

print("""
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║       🏖️ Party Hunt GOA Events Parser 🏖️            ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
""")

# ============================================================================
# Шаг 1: Токен
# ============================================================================
print("📝 Проверка токена...")
try:
    token = json.load(open('firebase_tokens.json'))['idToken']
    print("✅ Токен готов\n")
except:
    print("❌ Получаю новый токен...")
    os.system("python backend/api_analyzer/firebase_anonymous_auth.py > /dev/null 2>&1")
    token = json.load(open('firebase_tokens.json'))['idToken']

# ============================================================================
# Шаг 2: Парсинг ВСЕХ событий (с фильтрацией Goa)
# ============================================================================
print("🔥 Парсинг событий из Goa...\n")

all_docs = []
goa_count = 0
page = 1
next_token = None

url = "https://firestore.googleapis.com/v1/projects/partyhunt-production/databases/(default)/documents/events"
headers = {"Authorization": f"Bearer {token}"}

while page <= 100:  # Макс 100 страниц = 10000 событий
    params = {"pageSize": 100}
    if next_token:
        params["pageToken"] = next_token
    
    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
        if r.status_code != 200:
            print(f"❌ Ошибка {r.status_code}")
            break
        
        data = r.json()
        docs = data.get('documents', [])
        if not docs:
            break
        
        # Фильтр: только Goa
        goa_docs = []
        for doc in docs:
            tribe = doc.get('fields', {}).get('tribe', {}).get('stringValue', '')
            if tribe.lower() == 'goa':
                goa_docs.append(doc)
        
        all_docs.extend(goa_docs)
        goa_count += len(goa_docs)
        
        print(f"📄 Страница {page}: {len(goa_docs)} событий из Goa (всего проверено {len(docs)})")
        sys.stdout.flush()
        
        next_token = data.get('nextPageToken')
        if not next_token:
            print("\n✅ Все страницы проверены!")
            break
        
        page += 1
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        break

print(f"\n🎉 Найдено событий в Goa: {goa_count}\n")

# ============================================================================
# Шаг 3: Преобразование
# ============================================================================
print("🔧 Преобразование данных...")

def parse_val(v):
    if 'stringValue' in v: return v['stringValue']
    if 'integerValue' in v: return int(v['integerValue'])
    if 'doubleValue' in v: return float(v['doubleValue'])
    if 'booleanValue' in v: return v['booleanValue']
    if 'timestampValue' in v: return v['timestampValue']
    if 'arrayValue' in v:
        return [parse_val(x) for x in v['arrayValue'].get('values', [])]
    return None

events = []
for doc in all_docs:
    event = {k: parse_val(v) for k, v in doc.get('fields', {}).items()}
    event['id'] = doc['name'].split('/')[-1]
    events.append(event)

print(f"✅ Преобразовано {len(events)} событий\n")

# ============================================================================
# Шаг 4: Сохранение
# ============================================================================
print("💾 Создание файлов...")

os.makedirs('docs', exist_ok=True)

# Только events_goa.json
with open('docs/events_goa.json', 'w', encoding='utf-8') as f:
    json.dump({
        "city": "goa",
        "total": len(events),
        "updated_at": datetime.now().isoformat(),
        "events": events
    }, f, indent=2, ensure_ascii=False)

print(f"✅ events_goa.json ({len(events)} событий)")

# index.html - простая версия
html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏖️ Goa Party Events</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{
            background: white;
            border-radius: 20px;
            padding: 60px 40px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            margin-bottom: 30px;
        }}
        h1 {{
            font-size: 56px;
            background: linear-gradient(135deg, #f093fb, #f5576c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 40px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .stat-number {{
            font-size: 64px;
            font-weight: bold;
            background: linear-gradient(135deg, #f093fb, #f5576c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .content {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            margin-bottom: 30px;
        }}
        .api-link {{
            background: linear-gradient(135deg, #f093fb, #f5576c);
            color: white;
            text-decoration: none;
            padding: 20px 40px;
            border-radius: 10px;
            display: inline-block;
            font-size: 18px;
            font-weight: bold;
            transition: transform 0.3s;
            margin: 20px 0;
        }}
        .api-link:hover {{ transform: scale(1.05); }}
        pre {{
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
            border-radius: 10px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏖️ Goa Parties</h1>
            <p style="color: #666; font-size: 18px; margin-top: 10px;">Все вечеринки в Goa</p>
            <p style="color: #999; font-size: 14px; margin-top: 10px;">Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="total">{len(events)}</div>
                <div style="color: #666; margin-top: 10px; font-size: 18px;">Событий в Goa</div>
            </div>
        </div>

        <div class="content">
            <h2 style="border-bottom: 3px solid #f5576c; padding-bottom: 10px; margin-bottom: 20px;">📡 API Endpoint</h2>
            <div style="text-align: center;">
                <a href="events_goa.json" class="api-link">📥 events_goa.json</a>
            </div>
            <p style="color: #666; text-align: center; margin-top: 20px;">
                Прямая ссылка: <code>https://ваш-username.github.io/repo/events_goa.json</code>
            </p>
        </div>

        <div class="content">
            <h2 style="border-bottom: 3px solid #f5576c; padding-bottom: 10px; margin-bottom: 20px;">💻 Пример использования</h2>
            <pre>import requests

# Получить все события Goa
url = 'https://ваш-username.github.io/repo/events_goa.json'
response = requests.get(url)
data = response.json()

print(f"Событий в Goa: {{data['total']}}")

for event in data['events']:
    title = event.get('title', 'N/A')
    date = event.get('fromDate', 'N/A')
    print(f"- {{title}} ({{date}})")</pre>
        </div>

        <div style="text-align: center; color: white; padding: 20px; margin-top: 30px;">
            <p style="font-size: 18px;">🔥 Goa Party Hunt API</p>
            <p style="opacity: 0.8; margin-top: 10px;">Обновляется при запуске scrape_goa.py</p>
        </div>
    </div>

    <script>
        fetch('events_goa.json')
            .then(r => r.json())
            .then(data => {{
                document.getElementById('total').textContent = data.total.toLocaleString();
            }});
    </script>
</body>
</html>"""

with open('docs/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ index.html")

# README
readme = f"""# 🏖️ Goa Party Events API

Автоматически обновляемая база вечеринок в Goa из Party Hunt.

## 📊 Статистика

- **Событий в Goa:** {len(events)}
- **Обновлено:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

## 🚀 API

```
https://ваш-username.github.io/repo/events_goa.json
```

## 📖 Структура

```json
{{
  "city": "goa",
  "total": {len(events)},
  "updated_at": "2025-01-21T...",
  "events": [
    {{
      "id": "...",
      "title": "...",
      "fromDate": "...",
      "tribe": "goa",
      ...
    }}
  ]
}}
```

## 🔄 Обновление

```bash
python scrape_goa.py
```
"""

with open('docs/README.md', 'w', encoding='utf-8') as f:
    f.write(readme)

print("✅ README.md\n")

# ============================================================================
# ГОТОВО!
# ============================================================================
print("="*60)
print("✅ ГОТОВО!")
print("="*60)
print(f"""
📦 Файлы созданы:
   - docs/events_goa.json ({len(events)} событий, {round(os.path.getsize('docs/events_goa.json')/1024/1024, 1)} MB)
   - docs/index.html (красивая страница)
   - docs/README.md

🚀 Следующие шаги:

1. Откройте в браузере:
   open docs/index.html

2. Загрузите на GitHub:
   - Создайте репозиторий на github.com
   - Загрузите папку docs/
   - Включите GitHub Pages (Settings → Pages → /docs)

3. Ваш API будет:
   https://ваш-username.github.io/repo/events_goa.json

🔄 Обновлять данные:
   python scrape_goa.py
""")

