import pandas as pd
from atlassian import Confluence
from tabulate import tabulate
import re
from bs4 import BeautifulSoup

my_conflu = Confluence(
    url='https://confluence.sportsapi.ru/',
    username='kyuosipov',
    password='Mov@lis282'
)

def get_all_child_pages(my_conflu, parent_page_id, output_file):
    child_pages = my_conflu.get_child_pages(parent_page_id)
    for child_page in child_pages:
        content = my_conflu.get_page_by_id(child_page['id'], 'version.by.username', status=None)
        author = str(content['version']['by']['displayName'])
        print(author)
        status = my_conflu.get_page_by_id(child_page['id'], 'version,body.view', status=None, version=None)
        html_status = (str(status['body']['view']['value']))
        soup = BeautifulSoup(html_status, 'html.parser')
        # Находим элемент с классом "status-macro"
        status_element = soup.find(class_='status-macro')
        if status_element: 
            # Получаем текстовое содержимое этого элемента
            status_value = status_element.get_text()
        else: status_value = 'None'
        # Добавляем значения параметров в таблицу
        output_file.write(f"{child_page['title']},{author},{status_value}, https://confluence.sportsapi.ru/pages/viewpage.action?pageId={child_page['id']}\n")
        # Рекурсивный вызов для обработки дочерних страниц
        get_all_child_pages(my_conflu, child_page['id'], output_file)

parent_page_ids = pd.DataFrame({
    "page_id": ['261018044', '209226089', '249268548'],
    "supplier": ["1Set_Vol_Kos", "LSLive.Волейбол.Весь матч", "Руслан_Волейбол_ВесьМатч"]
})

#давай найдем список частей события по волейболу у других поставщиков?

main_df = pd.DataFrame()
my_df = pd.DataFrame()
for index, row in parent_page_ids.iterrows():
    page=row['page_id']
    supplier = row['supplier']
    page_title=(my_conflu.get_page_by_id(page)['title'])
    child_pages = my_conflu.get_child_pages(page)
    for index, page in enumerate(child_pages):
        child_page_title = page['title']
        child_page_id = page['id']
        content = my_conflu.get_page_by_id(child_page_id, 'version,body.view', status=None, version=None)
        html_content = str(content['body']['view']['value'])
        soup = BeautifulSoup(html_content, 'html.parser')
        position_key = soup.find('th', text='Позиция')
        if position_key:
            position_value = int(position_key.find_next('td').text.strip())
        else:
            position_value = None
        supplier_key = soup.find('th', text='ID пари у поставщика')
        if supplier_key:
            supplier_value = supplier_key.find_next('td').text.strip()
        else:
            supplier_value = None
        my_df = my_df._append([{#'Title': page_title,
                           #'Supplier': supplier,
                           'Child_name': child_page_title,
                           'Position': "{:04d}".format(position_value),
                           'Supplier_ID': supplier_value }], ignore_index=True)
        my_df = my_df.sort_values(by='Position', ignore_index=True)
    my_df.columns = my_df.columns + '_' + supplier
    main_df = main_df.join(my_df, how='outer')
    print(main_df.shape)
    my_df = pd.DataFrame()
#sorted_df = my_df.sort_values(by='Position')
main_df.to_csv('file.csv', index=False)