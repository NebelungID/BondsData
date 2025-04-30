ТЕХНИЧЕСКОЕ ЗАДАНИЕ

Описание задачи
Написан Python-скрипт для парсинга данных об облигациях с сайта Finam Bonds (https://bonds.finam.ru/issue/search/default.asp?page=0&showEmitter=1&showStatus=&showSector=&showTime=&showOperator=&showMoney=&showYTM=&showLiquid=&emitterCustomName=&status=4&sectorId=&FieldId=0&placementFrom=1%2F1%2F2025&placementTo=&paymentFrom=30%2F4%2F2027&paymentTo=&registrationDateFrom=&registrationDateTo=&couponRateFrom=10&couponRateTo=100&couponDateFrom=&couponDateTo=&offerExecDateFrom=&offerExecDateTo=&currencyId=1&volumeFrom=&volumeTo=&faceValueSign=&faceValue=&operatorId=0&operatorIdName=&opemitterCustomName=&operatorTypeId=0&operatorTypeName=&amortization=0&registrationDate=&regNumber=&govRegBody=&emissionForm1=&emissionForm2=&leaderDateFrom=&leaderDateTo=&placementMethod=0&quoteType=1&YTMOffer=on&YTMFrom=&YTMTo=&liquidRange=0&isRPS=0&liquidFrom=&liquidTo=&transactionsFrom=&transactionsTo=&liquidType=0&liquidTop=3&rating=&orderby=-2&is_finam_placed=). Скрипт извлекает информацию об облигациях, соответствующих заданным критериям.

Реализованные функции
1. Сбор данных об облигациях:
   - Полное наименование облигации (Колонка Выпуск)
   - Дата размещения облигации (формат: ГГГГ-ММ-ДД, Колонка Размещение)
   - Дата погашения облигации (формат: ГГГГ-ММ-ДД, Колонка Погашение)
   - Ссылка на страницу облигации (открывается при нажатии на название облигации)

2. Технические особенности реализации:
   - Использование Selenium WebDriver для обработки динамически генерируемого контента
   - Автоматическая обработка пагинации
   - Поиск таблицы с облигациями по наличию столбца '№'
   - Преобразование относительных ссылок в абсолютные
   - Конвертация дат из формата ДД.ММ.ГГГГ в ГГГГ-ММ-ДД

3. Обработка ошибок и логирование:
   - Все действия логируются в файл scraper.log
   - Реализована обработка исключительных ситуаций
   - Логирование процесса поиска и обработки таблиц
   - Отслеживание успешности формирования ссылок на облигации

4. Сохранение результатов:
   - Данные сохраняются в файл ./output/bonds_data.csv
   - Формат файла CSV с разделителем ";"
   - Кодировка UTF-8
   - Автоматическое создание директории output при необходимости

Технические требования
Используемые библиотеки Python:
- Selenium для обработки динамических элементов страницы
- BeautifulSoup для парсинга HTML
- pandas для работы с данными и сохранения в CSV
- webdriver_manager для автоматической установки ChromeDriver
- logging для ведения логов

Настройки WebDriver:
- Режим headless для фоновой работы
- Отключение ненужных функций браузера
- Настройка размера окна и пользовательского агента
- Отключение автоматизации для обхода защиты

Дополнительные условия
- Скрипт выполняется однократно, без циклического повторения
- Реализована проверка наличия данных на каждой странице
- Автоматическое завершение работы при достижении конца списка
- Корректное закрытие WebDriver при завершении работы

Инструкция по запуску
1. Установка зависимостей:
   ```
   pip install -r requirements.txt
   ```

2. Запуск скрипта:
   ```
   python bonds_scraper.py
   ```

3. Результаты работы:
   - Собранные данные будут сохранены в файл ./output/bonds_data.csv
   - Логи выполнения будут записаны в файл scraper.log
   - В случае ошибок, подробная информация будет доступна в логах

4. Требования к системе:
   - Установленный Python 3.x
   - Установленный Google Chrome
   - Доступ в интернет
   - Достаточно свободного места на диске для сохранения результатов

