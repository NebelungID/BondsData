import os
import logging
import time
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class BondsScraper:
    def __init__(self):
        self.base_url = "https://bonds.finam.ru/issue/search/default.asp?page=0&showEmitter=1&showStatus=&showSector=&showTime=&showOperator=&showMoney=&showYTM=&showLiquid=&emitterCustomName=&status=4&sectorId=&FieldId=0&placementFrom=1%2F1%2F2025&placementTo=&paymentFrom=30%2F4%2F2027&paymentTo=&registrationDateFrom=&registrationDateTo=&couponRateFrom=10&couponRateTo=100&couponDateFrom=&couponDateTo=&offerExecDateFrom=&offerExecDateTo=&currencyId=1&volumeFrom=&volumeTo=&faceValueSign=&faceValue=&operatorId=0&operatorIdName=&opemitterCustomName=&operatorTypeId=0&operatorTypeName=&amortization=0&registrationDate=&regNumber=&govRegBody=&emissionForm1=&emissionForm2=&leaderDateFrom=&leaderDateTo=&placementMethod=0&quoteType=1&YTMOffer=on&YTMFrom=&YTMTo=&liquidRange=0&isRPS=0&liquidFrom=&liquidTo=&transactionsFrom=&transactionsTo=&liquidType=0&liquidTop=3&rating=&orderby=-2&is_finam_placed="
        self.site_base_url = "https://bonds.finam.ru"
        self.output_dir = "./output"
        self.output_file = os.path.join(self.output_dir, "bonds_data.csv")
        self.setup_driver()

    def setup_driver(self):
        """Настройка Selenium WebDriver для Chrome"""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-webgl")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--enable-javascript")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        logging.info("Драйвер Chrome успешно инициализирован")

    def create_output_directory(self):
        """Создание директории для выходных файлов"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logging.info(f"Создана директория для выходных файлов: {self.output_dir}")

    def find_bonds_table(self, soup):
        """Поиск таблицы с облигациями по наличию столбца '№'"""
        tables = soup.find_all('table')
        logging.info(f"Найдено таблиц на странице: {len(tables)}")
        
        for i, table in enumerate(tables):
            # Проверяем заголовки таблицы
            headers = table.find_all('th')
            header_texts = [header.get_text(strip=True) for header in headers]
            logging.info(f"Таблица {i+1} заголовки: {header_texts}")
            
            # Проверяем наличие столбца '№'
            if '№' in header_texts:
                logging.info(f"Найдена таблица с облигациями (таблица {i+1})")
                return table
        
        logging.warning("Таблица с облигациями не найдена")
        return None

    def parse_bond_data(self, row):
        """Парсинг данных облигации из строки таблицы"""
        try:
            # Пропускаем строку, если это заголовок
            if row.find('th'):
                return None
                
            cells = row.find_all('td')
            if len(cells) < 4:
                return None

            # Извлечение названия облигации и ссылки
            bond_cell = cells[1]
            bond_name = bond_cell.get_text(strip=True)
            
            # Получаем относительную ссылку и преобразуем её в абсолютную
            link_element = bond_cell.find('a')
            if link_element and 'href' in link_element.attrs:
                relative_link = link_element['href']
                bond_link = urljoin(self.site_base_url, relative_link)
                logging.info(f"Сформирована ссылка для облигации {bond_name}: {bond_link}")
            else:
                bond_link = ''
                logging.warning(f"Не найдена ссылка для облигации {bond_name}")

            # Извлечение дат
            placement_date = cells[3].get_text(strip=True)  # Размещение
            maturity_date = cells[4].get_text(strip=True)   # Погашение

            # Конвертация дат в формат YYYY-MM-DD
            try:
                placement_date = datetime.strptime(placement_date, '%d.%m.%Y').strftime('%Y-%m-%d')
                maturity_date = datetime.strptime(maturity_date, '%d.%m.%Y').strftime('%Y-%m-%d')
            except ValueError as e:
                logging.warning(f"Не удалось распарсить даты для облигации {bond_name}: {str(e)}")
                return None

            return {
                'bond_name': bond_name,
                'placement_date': placement_date,
                'maturity_date': maturity_date,
                'bond_link': bond_link
            }
        except Exception as e:
            logging.error(f"Ошибка при парсинге данных облигации: {str(e)}")
            return None

    def scrape_page(self, page_number):
        """Сбор данных со страницы облигаций"""
        url = self.base_url.replace("page=0", f"page={page_number}")
        logging.info(f"Начало сбора данных со страницы {page_number}")
        
        try:
            self.driver.get(url)
            logging.info(f"Загрузка страницы {page_number}")
            time.sleep(5)  # Ожидание загрузки страницы
            
            # Получаем HTML страницы
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Ищем таблицу с облигациями
            table = self.find_bonds_table(soup)
            if not table:
                logging.error(f"Таблица с облигациями не найдена на странице {page_number}")
                return []
            
            # Поиск строк в таблице
            rows = table.find_all('tr')
            if not rows:
                logging.warning(f"На странице {page_number} не найдено строк в таблице")
                return []
            
            bonds_data = []
            for row in rows:
                bond_data = self.parse_bond_data(row)
                if bond_data:
                    bonds_data.append(bond_data)
                    logging.info(f"Обработана облигация: {bond_data['bond_name']}")
            
            logging.info(f"На странице {page_number} найдено {len(bonds_data)} облигаций")
            return bonds_data
        except Exception as e:
            logging.error(f"Ошибка при сборе данных со страницы {page_number}: {str(e)}")
            return []

    def save_to_csv(self, data):
        """Сохранение данных в CSV файл"""
        df = pd.DataFrame(data)
        df.to_csv(self.output_file, sep=';', index=False, encoding='utf-8')
        logging.info(f"Данные сохранены в файл {self.output_file}")

    def run(self):
        """Основной метод выполнения"""
        try:
            self.create_output_directory()
            all_bonds_data = []
            page_number = 0
            
            while True:
                bonds_data = self.scrape_page(page_number)
                if not bonds_data:
                    logging.info(f"Достигнут конец списка облигаций на странице {page_number}")
                    break
                
                all_bonds_data.extend(bonds_data)
                logging.info(f"Обработана страница {page_number}, найдено {len(bonds_data)} облигаций")
                page_number += 1
            
            if all_bonds_data:
                self.save_to_csv(all_bonds_data)
                logging.info(f"Всего обработано {len(all_bonds_data)} облигаций")
            else:
                logging.warning("Не удалось собрать данные об облигациях")
                
        except Exception as e:
            logging.error(f"Критическая ошибка при выполнении скрипта: {str(e)}")
        finally:
            self.driver.quit()
            logging.info("Работа скрипта завершена")

if __name__ == "__main__":
    logging.info("Запуск скрипта для сбора данных об облигациях")
    scraper = BondsScraper()
    scraper.run() 