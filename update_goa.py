#!/usr/bin/env python3
"""
🏖️ Обновление данных Goa

Запускайте когда нужно обновить сайт:
python update_goa.py
"""
import requests, json, os, sys
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("""
╔════════════════════════════════════════════════╗
║                                                ║
║     🏖️ Party Hunt Goa Update Script 🏖️       ║
║                                                ║
╚════════════════════════════════════════════════╝
""")

# ============================================================================
# Шаг 1: Получить свежий токен
# ============================================================================
print("1️⃣  Получение токена Firebase...")

API_KEY = "AIzaSyDyyJBEElD1YC3mzttkiZoY4RqeMgkAAlA"
AUTH_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"

response = requests.post(AUTH_URL, json={"returnSecureToken": True}, timeout=10)
if response.status_code != 200:
    print(f"❌ Ошибка получения токена: {response.status_code}")
    sys.exit(1)

token = response.json()['idToken']
print("✅ Токен получен\n")

# ============================================================================
# Шаг 2: Парсинг событий Goa
# ============================================================================
print("2️⃣  Парсинг событий Goa из Firestore...")
print("="*60)

def parse_val(v):
    if 'stringValue' in v: return v['stringValue']
    if 'integerValue' in v: return int(v['integerValue'])
    if 'booleanValue' in v: return v['booleanValue']
    if 'timestampValue' in v: return v['timestampValue']
    if 'arrayValue' in v:
        arr = [parse_val(x) for x in v['arrayValue'].get('values', []) if x]
        return [x for x in arr if x is not None]
    return None

FIELDS = {'eventName', 'description', 'fromDate', 'toDate', 'picture', 'picture_thumbnail',
          'tribe', 'idPlace', 'placeName', 'entryFee', 'listTags', 'viewsCount', 'commentsCount',
          'totalCheckin', 'countFollowers', 'publishStatus', 'isFeatured', 'docId'}

goa_events = []
page, next_token = 1, None

url = "https://firestore.googleapis.com/v1/projects/partyhunt-production/databases/(default)/documents/events"
headers = {"Authorization": f"Bearer {token}"}

while page <= 100:
    params = {"pageSize": 100}
    if next_token: params["pageToken"] = next_token
    
    r = requests.get(url, headers=headers, params=params, timeout=30)
    if r.status_code != 200:
        print(f"❌ Ошибка {r.status_code}")
        break
    
    data = r.json()
    docs = data.get('documents', [])
    if not docs: break
    
    # Только Goa
    for doc in docs:
        fields = doc.get('fields', {})
        if fields.get('tribe', {}).get('stringValue', '').lower() == 'goa':
            event = {}
            for fname in FIELDS:
                if fname in fields:
                    val = parse_val(fields[fname])
                    if val:
                        event['title' if fname == 'eventName' else fname] = val
            event['id'] = doc['name'].split('/')[-1]
            if event: goa_events.append(event)
    
    goa_count = len([d for d in docs if d.get('fields', {}).get('tribe', {}).get('stringValue', '').lower() == 'goa'])
    print(f"Стр {page}: +{goa_count} Goa | Всего: {len(goa_events)}")
    sys.stdout.flush()
    
    next_token = data.get('nextPageToken')
    if not next_token:
        print("\n✅ Все события получены!")
        break
    page += 1

print(f"\n🎉 Всего: {len(goa_events)} событий\n")

# ============================================================================
# Шаг 3: Сохранение
# ============================================================================
print("3️⃣  Сохранение данных...")

os.makedirs('docs', exist_ok=True)

data = {
    "city": "goa",
    "total": len(goa_events),
    "updated_at": datetime.now().isoformat(),
    "events": goa_events
}

with open('docs/events_goa.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

size_mb = os.path.getsize('docs/events_goa.json') / 1024 / 1024
print(f"✅ events_goa.json ({size_mb:.1f} MB)\n")

# ============================================================================
# Готово!
# ============================================================================
print("="*60)
print("✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!")
print("="*60)
print(f"""
📦 Файлы обновлены:
   docs/events_goa.json - {len(goa_events)} событий

🚀 Следующие шаги:

1. Откройте сайт локально:
   open docs/index.html

2. Загрузите на GitHub (если еще не загружено):
   - Зайдите на github.com
   - Создайте репозиторий
   - Upload папку docs/
   - Включите GitHub Pages

3. Ваш парсер сможет парсить:
   https://ваш-username.github.io/repo/events_goa.json

🔄 Запускайте этот скрипт когда нужно обновить данные!
""")

