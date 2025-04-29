import os
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import sys
import locale
import re

# Устанавливаем кодировку для логов
locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bonds_parser.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class BondsParser:
    def __init__(self):
        self.base_url = "https://bonds.finam.ru/issue/search/default.asp?page={}&showEmitter=1&showStatus=&showSector=&showTime=&showOperator=&showMoney=&showYTM=&showLiquid=&emitterCustomName=&status=4&sectorId=&FieldId=0&placementFrom=1%2F1%2F2022&placementTo=1%2F7%2F2028&paymentFrom=&paymentTo=&registrationDateFrom=&registrationDateTo=&couponRateFrom=&couponRateTo=&couponDateFrom=&couponDateTo=&offerExecDateFrom=&offerExecDateTo=&currencyId=0&volumeFrom=&volumeTo=&faceValueSign=&faceValue=&operatorId=0&operatorIdName=&opemitterCustomName=&operatorTypeId=0&operatorTypeName=&amortization=0&registrationDate=&regNumber=&govRegBody=&emissionForm1=&emissionForm2=&leaderDateFrom=&leaderDateTo=&placementMethod=0&quoteType=1&YTMOffer=on&YTMFrom=&YTMTo=&liquidRange=0&isRPS=0&liquidFrom=&liquidTo=&transactionsFrom=&transactionsTo=&liquidType=0&liquidTop=0&rating=&orderby=-2&is_finam_placed="
        self.output_dir = "output"
        self.bonds_data = []  # Список для хранения данных об облигациях
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36")
            
            chrome_options.add_argument("--lang=ru")
            chrome_options.add_argument("--accept-lang=ru")
            
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME')),
            ]
            
            chrome_path = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_path = path
                    break
            
            if chrome_path:
                chrome_options.binary_location = chrome_path
                logging.info(f"Найден Chrome по пути: {chrome_path}")
            else:
                logging.warning("Chrome не найден в стандартных местах")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            
            self.wait = WebDriverWait(self.driver, 30)  # Увеличиваем время ожидания до 30 секунд
            
        except Exception as e:
            logging.error(f"Ошибка при инициализации WebDriver: {str(e)}")
            logging.error("Пожалуйста, убедитесь, что:")
            logging.error("1. Google Chrome установлен на вашем компьютере")
            logging.error("2. Версия Chrome совместима с версией ChromeDriver")
            logging.error("3. У вас есть права на запуск Chrome")
            sys.exit(1)
            
    def find_bonds_table(self):
        """Поиск таблицы с облигациями среди всех таблиц на странице"""
        try:
            # Сначала проверяем загрузку страницы
            self.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logging.info("Страница загружена")
            
            # Ждем немного для полной загрузки
            time.sleep(5)
            
            # Ищем все таблицы
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            logging.info(f"Найдено {len(tables)} таблиц на странице")
            
            # Проверяем каждую таблицу
            for i, table in enumerate(tables):
                try:
                    # Получаем заголовки таблицы
                    headers = table.find_elements(By.TAG_NAME, "th")
                    if not headers:
                        headers = table.find_elements(By.TAG_NAME, "td")
                        
                    if not headers:
                        continue
                        
                    # Проверяем первый заголовок
                    first_header = headers[0].text.strip()
                    logging.info(f"Первый заголовок таблицы #{i+1}: {first_header}")
                    
                    if first_header == "№":
                        logging.info(f"Найдена таблица с облигациями (таблица #{i+1})")
                        return table
                        
                except Exception as e:
                    logging.warning(f"Ошибка при проверке таблицы #{i+1}: {str(e)}")
                    continue
                    
            logging.error("Не удалось найти таблицу с облигациями")
            return None
            
        except Exception as e:
            logging.error(f"Ошибка при поиске таблицы: {str(e)}")
            return None
            
    def get_bond_details(self, bond_link):
        """Получение дополнительной информации об облигации со страницы"""
        try:
            logging.info(f"Переход на страницу облигации: {bond_link}")
            self.driver.get(bond_link)
            
            # Ждем загрузки страницы
            self.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)  # Ждем полной загрузки
            
            details = {
                'ISIN': '',
                'Статус': '',
                'Есть_платежи': 'Нет',
                'Есть_оферты': 'Нет'
            }
            
            try:
                # Ищем ISIN
                isin_element = self.driver.find_element(By.XPATH, "//td[contains(text(), 'ISIN')]/following-sibling::td")
                details['ISIN'] = isin_element.text.strip()
            except Exception as e:
                logging.warning(f"Не удалось найти ISIN: {str(e)}")
                
            try:
                # Ищем статус
                status_element = self.driver.find_element(By.XPATH, "//td[contains(text(), 'Статус')]/following-sibling::td")
                details['Статус'] = status_element.text.strip()
            except Exception as e:
                logging.warning(f"Не удалось найти статус: {str(e)}")
                
            try:
                # Проверяем наличие вкладки "Платежи"
                payments_tab = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Платежи')]")
                details['Есть_платежи'] = 'Да'
            except Exception:
                details['Есть_платежи'] = 'Нет'
                
            try:
                # Проверяем наличие вкладки "Оферты"
                offers_tab = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Оферты')]")
                details['Есть_оферты'] = 'Да'
            except Exception:
                details['Есть_оферты'] = 'Нет'
                
            return details
            
        except Exception as e:
            logging.error(f"Ошибка при получении деталей облигации: {str(e)}")
            return None
            
    def parse_page(self, page_number):
        """Парсинг одной страницы с облигациями"""
        try:
            url = self.base_url.format(page_number)
            logging.info(f"Переход на страницу: {url}")
            self.driver.get(url)
            
            try:
                # Ждем загрузки страницы
                self.wait.until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                logging.info("Страница успешно загружена")
                
                # Ждем немного для полной загрузки
                time.sleep(5)
                
            except Exception as e:
                logging.error(f"Ошибка при загрузке страницы: {str(e)}")
                return
                
            try:
                table = self.find_bonds_table()
                if not table:
                    return
                    
                # Получаем все строки таблицы, кроме заголовка
                rows = table.find_elements(By.TAG_NAME, "tr")[1:]
                logging.info(f"Найдено {len(rows)} строк в таблице")
                
                if not rows:
                    logging.warning("Таблица пуста")
                    return
                    
                for row in rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) < 6:  # Проверяем, что есть все необходимые колонки
                            continue
                            
                        # Получаем данные из нужных колонок
                        bond_name_cell = cells[1]
                        bond_name = bond_name_cell.text.strip()  # Название облигации
                        
                        # Получаем ссылку на страницу облигации
                        bond_link = ""
                        try:
                            link_element = bond_name_cell.find_element(By.TAG_NAME, "a")
                            bond_link = link_element.get_attribute("href")
                        except Exception as e:
                            logging.warning(f"Не удалось получить ссылку для облигации {bond_name}: {str(e)}")
                        
                        # Проверяем, что это не служебная строка
                        if (bond_name and 
                            re.search('[а-яА-Я]', bond_name) and
                            not any(text in bond_name.lower() for text in [
                                "название облигации",
                                "от:",
                                "до:",
                                "размещение",
                                "найдено выпусков",
                                "параметры поиска",
                                "фильтр",
                                "в обращении",
                                "поиск выпусков",
                                "календарь"
                            ])):
                            
                            # Получаем детали облигации
                            bond_details = self.get_bond_details(bond_link) if bond_link else {}
                            
                            # Собираем данные об облигации
                            bond_data = {
                                'Название': bond_name,
                                'Дата размещения': cells[2].text.strip(),
                                'Дата погашения': cells[3].text.strip(),
                                'Объем': cells[4].text.strip(),
                                'Валюта': cells[5].text.strip(),
                                'Ссылка': bond_link,
                                'ISIN': bond_details.get('ISIN', ''),
                                'Статус': bond_details.get('Статус', ''),
                                'Есть_платежи': bond_details.get('Есть_платежи', 'Нет'),
                                'Есть_оферты': bond_details.get('Есть_оферты', 'Нет')
                            }
                            
                            self.bonds_data.append(bond_data)
                            logging.info(f"Добавлена облигация: {bond_name}")
                            
                            # Возвращаемся на страницу со списком облигаций
                            self.driver.get(url)
                            time.sleep(3)
                                
                    except Exception as e:
                        logging.error(f"Ошибка при парсинге строки: {str(e)}")
                        continue
                        
            except Exception as e:
                logging.error(f"Ошибка при работе с таблицей: {str(e)}")
                return
                
        except Exception as e:
            logging.error(f"Ошибка при парсинге страницы {page_number}: {str(e)}")
            
    def parse_bonds(self):
        try:
            logging.info("Начало парсинга списка облигаций")
            
            for page in range(2):  # Парсим только 2 страницы
                logging.info(f"Парсинг страницы {page + 1}")
                self.parse_page(page)
                
            self.save_results()
            
        except Exception as e:
            logging.error(f"Ошибка при парсинге: {str(e)}")
        finally:
            self.driver.quit()
            
    def save_results(self):
        try:
            if not self.bonds_data:
                logging.warning("Нет данных для сохранения")
                return
                
            # Создаем DataFrame из списка словарей
            df = pd.DataFrame(self.bonds_data)
            
            output_path = os.path.join(self.output_dir, 'bonds_list.csv')
            df.to_csv(output_path, sep=';', index=False, encoding='utf-8')
            logging.info(f"Список облигаций сохранен в файл: {output_path}")
            logging.info(f"Всего найдено {len(self.bonds_data)} облигаций")
            
        except Exception as e:
            logging.error(f"Ошибка при сохранении результатов: {str(e)}")

if __name__ == "__main__":
    parser = BondsParser()
    parser.parse_bonds() 