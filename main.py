import os
import re
import pandas as pd
from atlassian import Confluence
from tabulate import tabulate
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("script.log", encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# Загрузка .env
load_dotenv()

url = os.getenv("CONFLUENCE_URL")
username = os.getenv("CONFLUENCE_USERNAME")
password = os.getenv("CONFLUENCE_PASSWORD")

if not all([url, username, password]):
    logger.error("Не найдены переменные окружения. Проверь файл .env.")
    exit(1)

# Создаем клиент
logger.info("Создаём подключение к Confluence...")
my_conflu = Confluence(url=url, username=username, password=password)

def print_pretty_tree(confluence_client, page_id, file, prefix=""):
    try:
        page = confluence_client.get_page_by_id(page_id)
        title = page.get('title', '[без названия]')
        file.write(f"{prefix}├── {title} (ID: {page_id})\n")

        children = list(confluence_client.get_child_pages(page_id))  # 💡 фикс здесь
        total = len(children)

        for i, child in enumerate(children):
            is_last = (i == total - 1)
            new_prefix = prefix + ("    " if is_last else "│   ")
            print_pretty_tree(confluence_client, child['id'], file, new_prefix)
    except Exception as e:
        file.write(f"{prefix}├── [Ошибка при обработке страницы {page_id}: {e}]\n")


def print_page_tree(confluence_client, page_id, level=0):
    try:
        page = confluence_client.get_page_by_id(page_id)
        title = page.get('title', '[без названия]')
        indent = "    " * level
        logger.info(f"{indent}- {title} (ID: {page_id})")

        children = confluence_client.get_child_pages(page_id)
        for child in children:
            print_page_tree(confluence_client, child['id'], level + 1)
    except Exception as e:
        logger.error(f"Ошибка при обработке страницы {page_id}: {e}")

# Получение дочерних страниц с рекурсией
def get_all_child_pages(my_conflu, parent_page_id, output_file):
    try:
        child_pages = my_conflu.get_child_pages(parent_page_id)
        for child_page in child_pages:
            content = my_conflu.get_page_by_id(child_page['id'], 'version.by.username')
            author = str(content['version']['by']['displayName'])
            logger.info(f"Автор: {author}")

            status = my_conflu.get_page_by_id(child_page['id'], 'version,body.view')
            html_status = str(status['body']['view']['value'])
            soup = BeautifulSoup(html_status, 'html.parser')
            status_element = soup.find(class_='status-macro')
            status_value = status_element.get_text() if status_element else 'None'

            url = f"https://confluence.sportsapi.ru/pages/viewpage.action?pageId={child_page['id']}"
            output_file.write(f"{child_page['title']},{author},{status_value},{url}\n")

            get_all_child_pages(my_conflu, child_page['id'], output_file)
    except Exception as e:
        logger.error(f"Ошибка при обработке дочерней страницы {parent_page_id}: {e}")

# Родительские страницы
parent_page_ids = pd.DataFrame({
    "page_id": ['261018044', '209226089', '249268548'],
    "supplier": ["1Set_Vol_Kos", "LSLive.Волейбол.Весь матч", "Руслан_Волейбол_ВесьМатч"]
})

main_df = pd.DataFrame()
my_df = pd.DataFrame()

for index, row in parent_page_ids.iterrows():
    page = row['page_id']
    supplier = row['supplier']
    logger.info(f"Обрабатываем поставщика: {supplier} (ID: {page})")

    try:
        page_title = my_conflu.get_page_by_id(page)['title']
        child_pages = my_conflu.get_child_pages(page)

        for index, page in enumerate(child_pages):
            child_page_title = page['title']
            child_page_id = page['id']
            content = my_conflu.get_page_by_id(child_page_id, 'version,body.view')
            html_content = str(content['body']['view']['value'])
            soup = BeautifulSoup(html_content, 'html.parser')

            position_key = soup.find('th', text='Позиция')
            position_value = int(position_key.find_next('td').text.strip()) if position_key else None

            supplier_key = soup.find('th', text='ID пари у поставщика')
            supplier_value = supplier_key.find_next('td').text.strip() if supplier_key else None

            my_df = my_df._append([{
                'Child_name': child_page_title,
                'Position': "{:04d}".format(position_value) if position_value is not None else None,
                'Supplier_ID': supplier_value
            }], ignore_index=True)

        my_df = my_df.sort_values(by='Position', ignore_index=True)
        my_df.columns = my_df.columns + '_' + supplier
        main_df = main_df.join(my_df, how='outer')
        logger.info(f"Данные по '{supplier}' добавлены. Размер main_df: {main_df.shape}")
        my_df = pd.DataFrame()

    except Exception as e:
        logger.error(f"Ошибка при обработке поставщика {supplier}: {e}")

# Финальный экспорт
main_df.to_csv('file.csv', index=False)
logger.info("Файл 'file.csv' успешно создан.")

logger.info("📄 Генерирую красивое дерево страниц в tree.txt...")
with open("tree.txt", "w", encoding="utf-8") as f:
    f.write(".\n")
    print_pretty_tree(my_conflu, "192101019", f)
logger.info("✅ Готово! Дерево сохранено в tree.txt")
