import pandas as pd
from atlassian import Confluence
from tabulate import tabulate
import re
from io import StringIO
from bs4 import BeautifulSoup

my_conflu = Confluence(
    url='https://confluence.sportsapi.ru/',
    username='kyuosipov',
    password='Mov@lis282'
)
##Получаем содержимое страницы
page_id = 261020412
content = my_conflu.get_page_by_id(page_id, 'version,body.view', status=None, version=None)
html_content = (str(content['body']['view']['value']))
soup = BeautifulSoup(html_content, 'html.parser')
# Найти все элементы в объекте BeautifulSoup
table_elements = soup.find_all('table', class_='wrapped confluenceTable')
# Получаем последнюю таблицу. Она с исходами.
outcome_table = table_elements[-1]
html_data = StringIO(str(outcome_table))
df = pd.read_html(html_data)[0]
# Выводим DataFrame
df.iloc[:, 1] = df.iloc[:, 0]
changed_table = df.to_html()
print(changed_table)
print(outcome_table)
outcome_table.extract()
soup.append(changed_table)
updated_html = soup.prettify()
