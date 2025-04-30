import os
import logging
import time
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
        logging.FileHandler('bonds_find.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class BondsFilter:
    def __init__(self, test_mode=False):
        # Настройки
        self.min_coupon_rate = 5.0  # Минимальный купонный доход в процентах
        self.input_file = "./output/bonds_data.csv"
        self.output_file = "./output/bonds_filter.csv"
        self.log_file = "bonds_filter.log"
        self.site_base_url = "https://bonds.finam.ru"
        self.test_mode = test_mode  # Режим тестирования
        
        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        # Инициализация WebDriver
        self.setup_driver()
        
        # Создание директории для выходных файлов
        self.create_output_directory()

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
        output_dir = os.path.dirname(self.output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logging.info(f"Создана директория для выходных файлов: {output_dir}")

    def get_isin(self, soup):
        """Получение ISIN кода облигации"""
        try:
            # Ищем div с классом "info"
            info_div = soup.find('div', class_='info')
            logging.info(f"Найден div с классом info: {info_div is not None}")
            
            if info_div:
                # Ищем все td в div
                tds = info_div.find_all('td')
                logging.info(f"Найдено td элементов: {len(tds)}")
                
                for td in tds:
                    # Проверяем, содержит ли td текст "ISIN код:"
                    if 'ISIN код:' in td.text:
                        logging.info(f"Найден td с ISIN код: {td.text}")
                        # Ищем span внутри найденного td
                        isin_span = td.find('span')
                        logging.info(f"Найден span с ISIN: {isin_span is not None}")
                        
                        if isin_span:
                            isin = isin_span.text.strip()
                            logging.info(f"Найден ISIN: {isin}")
                            return isin
            
            logging.warning("ISIN не найден")
            return None
        except Exception as e:
            logging.error(f"Ошибка при получении ISIN: {str(e)}")
            return None

    def check_offer(self, soup):
        """Проверка наличия оферты"""
        try:
            # Ищем элемент с текстом "Оферты"
            offer_element = soup.find('a', string='Оферты')
            if offer_element:
                logging.info("Найдена оферта")
                return True
            
            logging.info("Оферта не найдена")
            return False
        except Exception as e:
            logging.error(f"Ошибка при проверке оферты: {str(e)}")
            return False

    def get_coupon_rate(self, soup):
        """Получение ставки купона"""
        try:
            # Переход на вкладку "Платежи"
            payments_tab = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Платежи')]"))
            )
            payments_tab.click()
            time.sleep(3)  # Ожидание загрузки страницы
            
            # Получение обновленного HTML
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Поиск всех таблиц на странице
            tables = soup.find_all('table')
            logging.info(f"Найдено таблиц на странице: {len(tables)}")
            
            # Поиск таблицы с купонными платежами
            for i, table in enumerate(tables):
                # Проверяем заголовки таблицы
                headers = table.find_all('th')
                header_texts = [header.get_text(strip=True) for header in headers]
                logging.info(f"Таблица {i+1} заголовки: {header_texts}")
                
                # Ищем таблицу с колонкой "Ставка" во втором уровне заголовков
                if 'Купоны' in header_texts and 'Погашение' in header_texts:
                    # Находим все строки таблицы
                    rows = table.find_all('tr')
                    if len(rows) >= 2:  # Должны быть как минимум заголовки и одна строка данных
                        # Получаем заголовки второго уровня
                        second_level_headers = rows[1].find_all('th')
                        second_level_texts = [header.get_text(strip=True) for header in second_level_headers]
                        logging.info(f"Таблица {i+1} заголовки второго уровня: {second_level_texts}")
                        
                        # Находим индекс колонки "Ставка"
                        if 'Ставка' in second_level_texts:
                            rate_col_index = second_level_texts.index('Ставка')
                            
                            # Ищем первую строку с данными (пропускаем два уровня заголовков)
                            for row in rows[2:]:
                                cells = row.find_all('td')
                                if len(cells) > rate_col_index:
                                    try:
                                        rate_text = cells[rate_col_index].text.strip()
                                        if '%' in rate_text:
                                            rate = float(rate_text.replace('%', '').replace(',', '.'))
                                            logging.info(f"Найдена ставка купона: {rate}%")
                                            return rate
                                    except ValueError:
                                        continue
            return None
        except Exception as e:
            logging.error(f"Ошибка при получении ставки купона: {str(e)}")
            return None

    def process_bond(self, bond_data):
        """Обработка одной облигации"""
        try:
            # Переход на страницу облигации
            self.driver.get(bond_data['bond_link'])
            time.sleep(3)  # Ожидание загрузки страницы
            
            # Получение HTML страницы
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Сбор данных
            isin = self.get_isin(soup)
            has_offer = self.check_offer(soup)
            coupon_rate = self.get_coupon_rate(soup)
            
            # Проверка критериев
            if has_offer:
                logging.info(f"Облигация {bond_data['bond_name']} отбракована: имеет оферту")
                return None
                
            if coupon_rate is None:
                logging.info(f"Облигация {bond_data['bond_name']} отбракована: не удалось получить ставку купона")
                return None
                
            if coupon_rate < self.min_coupon_rate:
                logging.info(f"Облигация {bond_data['bond_name']} отбракована: ставка купона {coupon_rate}% ниже минимальной {self.min_coupon_rate}%")
                return None
            
            # Формирование результата в новом формате
            result = {
                'Название облигации': bond_data['bond_name'],
                'ISIN': isin,
                'Дата размещения': bond_data['placement_date'],
                'Дата погашения': bond_data['maturity_date'],
                'Ставка купона': f"{coupon_rate}%",
                'Ссылка': bond_data['bond_link']
            }
            
            logging.info(f"Облигация {bond_data['bond_name']} соответствует критериям")
            return result
            
        except Exception as e:
            logging.error(f"Ошибка при обработке облигации {bond_data['bond_name']}: {str(e)}")
            return None

    def run(self):
        """Основной метод выполнения"""
        try:
            # Чтение входного файла
            if not os.path.exists(self.input_file):
                logging.error(f"Входной файл не найден: {self.input_file}")
                return
                
            df = pd.read_csv(self.input_file, sep=';', encoding='utf-8')
            logging.info(f"Прочитано {len(df)} облигаций из файла {self.input_file}")
            
            # Берем только первую облигацию для тестирования
            df = df.head(1)
            logging.info("Тестируем только первую облигацию")
            
            # Обработка облигаций
            filtered_bonds = []
            for _, row in df.iterrows():
                bond_data = {
                    'bond_name': row['bond_name'],
                    'placement_date': row['placement_date'],
                    'maturity_date': row['maturity_date'],
                    'bond_link': row['bond_link']
                }
                
                processed_bond = self.process_bond(bond_data)
                if processed_bond:
                    filtered_bonds.append(processed_bond)
            
            # Сохранение результатов
            if filtered_bonds:
                result_df = pd.DataFrame(filtered_bonds)
                result_df.to_csv(self.output_file, sep=';', index=False, encoding='utf-8')
                logging.info(f"Сохранено {len(filtered_bonds)} облигаций в файл {self.output_file}")
            else:
                logging.warning("Не найдено облигаций, соответствующих критериям")
                
        except Exception as e:
            logging.error(f"Критическая ошибка при выполнении скрипта: {str(e)}")
        finally:
            self.driver.quit()
            logging.info("Работа скрипта завершена")

if __name__ == "__main__":
    logging.info("Запуск скрипта для фильтрации облигаций")
    filter = BondsFilter(test_mode=True)  # Включаем тестовый режим
    filter.run() 