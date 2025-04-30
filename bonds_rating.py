import csv
import requests
from bs4 import BeautifulSoup
import time
import logging

# Настраиваем логирование только для ошибок
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def get_bond_rating(isin):
    url = f"https://smart-lab.ru/q/bonds/{isin}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем блок с рейтингом по тексту
        rating_text = soup.find(string=lambda text: text and 'рейтинг' in text.lower())
        if not rating_text:
            return "Нет данных", "Нет данных"
            
        # Находим родительский div
        rating_parent = rating_text.find_parent('div')
        if not rating_parent:
            return "Нет данных", "Нет данных"
            
        # Ищем прогресс-бар с рейтингом
        progress_bar = rating_parent.find('div', class_='linear-progress-bar')
        if not progress_bar:
            # Пробуем найти в соседних элементах
            progress_bar = rating_parent.find_next('div', class_='linear-progress-bar')
            if not progress_bar:
                return "Нет данных", "Нет данных"
            
        # Получаем цвет и значение рейтинга
        rating_filled = progress_bar.find('div', class_='linear-progress-bar__filed')
        if not rating_filled:
            return "Нет данных", "Нет данных"
            
        # Определяем цвет
        color = "Нет данных"
        if 'linear-progress-bar__filed--red' in rating_filled.get('class', []):
            color = "Красный"
        elif 'linear-progress-bar__filed--yellow' in rating_filled.get('class', []):
            color = "Желтый"
        elif 'linear-progress-bar__filed--green' in rating_filled.get('class', []):
            color = "Зеленый"
            
        # Получаем значение рейтинга
        rating_text = rating_filled.find('div', class_='linear-progress-bar__text')
        rating = rating_text.get_text(strip=True) if rating_text else "Нет данных"
        
        return rating, color
        
    except Exception as e:
        logging.error(f"Ошибка при получении рейтинга для {isin}: {str(e)}")
        return "Ошибка", "Ошибка"

def process_bonds():
    input_file = 'output/bonds_filter.csv'
    output_file = 'output/bonds_with_ratings.csv'
    
    try:
        # Читаем заголовки из входного файла
        with open(input_file, 'r', encoding='utf-8') as infile:
            headers = next(csv.reader(infile, delimiter=';'))
            
        # Читаем все строки из входного файла
        with open(input_file, 'r', encoding='utf-8') as infile:
            rows = list(csv.reader(infile, delimiter=';'))
            rows = rows[1:]  # Пропускаем заголовки
            
        # Находим индекс колонки со ставкой и ссылкой
        link_index = len(headers) - 1  # Ссылка обычно последняя
        rate_index = link_index - 1    # Ставка перед ссылкой
        
        # Добавляем колонки рейтинга и цвета после ставки
        headers.insert(link_index, 'Рейтинг')
        headers.insert(link_index + 1, 'Цвет рейтинга')
        
        # Записываем результаты в выходной файл
        with open(output_file, 'w', encoding='utf-8-sig', newline='') as outfile:
            writer = csv.writer(outfile, delimiter=';')
            writer.writerow(headers)
            
            # Обрабатываем все облигации
            total_bonds = len(rows)
            for i, row in enumerate(rows):
                if len(row) >= 2:  # Проверяем наличие ISIN
                    isin = row[1]
                    if isin:  # Проверяем, что ISIN не пустой
                        print(f"Обработка облигации {i+1}/{total_bonds}: {row[0]} (ISIN: {isin})")
                        rating, color = get_bond_rating(isin)
                        # Вставляем рейтинг и цвет перед ссылкой
                        row.insert(link_index, rating)
                        row.insert(link_index + 1, color)
                        writer.writerow(row)
                        time.sleep(5)  # Задержка между запросами

    except Exception as e:
        logging.error(f"Ошибка при обработке файлов: {str(e)}")

if __name__ == '__main__':
    process_bonds() 