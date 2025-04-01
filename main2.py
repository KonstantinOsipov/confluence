import os
import requests
import csv
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

username = os.getenv("CONFLUENCE_USERNAME")
password = os.getenv("CONFLUENCE_PASSWORD")

page_id = "103981636"
base_url = "https://confluence.sportsapi.ru"
api_url = f"{base_url}/rest/api/content/{page_id}/child/page"

auth = (username, password)
headers = {
    "Accept": "application/json"
}

params = {
    "limit": 100,
    "expand": "history,version"
}

pages = []

while api_url:
    response = requests.get(api_url, auth=auth, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Ошибка {response.status_code}: {response.text}")
        break

    data = response.json()

    for result in data.get("results", []):
        title = result.get("title")
        pid = result.get("id")

        created = result.get("history", {}).get("createdDate", "N/A")
        author = result.get("history", {}).get("createdBy", {}).get("displayName", "N/A")

        last_updated = result.get("version", {}).get("when", "N/A")
        updater = result.get("version", {}).get("by", {}).get("displayName", "N/A")

        # Преобразуем дату для сортировки (если нужно)
        try:
            sort_date = datetime.fromisoformat(last_updated.rstrip("Z"))
        except Exception:
            sort_date = None

        pages.append({
            "Title": title,
            "Page ID": pid,
            "Created": created,
            "Author": author,
            "Last Updated": last_updated,
            "Last Updated By": updater,
            "_SortDate": sort_date
        })

        print(f"- {title} (ID: {pid}, Created: {created}, Updated: {last_updated}, By: {updater})")

    next_link = data.get("_links", {}).get("next")
    if next_link:
        api_url = base_url + next_link
        params = {}
    else:
        api_url = None

# Сортировка по дате последнего обновления (новее сверху)
pages.sort(key=lambda x: x["_SortDate"] or datetime.min, reverse=True)

# Сохраняем в CSV
csv_filename = "confluence_pages.csv"
with open(csv_filename, mode="w", encoding="utf-8", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=["Title", "Page ID", "Created", "Author", "Last Updated", "Last Updated By"])
    writer.writeheader()
    for row in pages:
        # Удаляем поле "_SortDate" перед записью
        row_copy = row.copy()
        del row_copy["_SortDate"]
        writer.writerow(row_copy)

print(f"\n✅ Найдено {len(pages)} страниц.")
print(f"✅ Сохранено в файл: {csv_filename} (отсортировано по дате изменения)")
