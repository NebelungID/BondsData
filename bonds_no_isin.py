import pandas as pd
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bonds_no_isin.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def find_bonds_without_isin():
    try:
        # Чтение исходного файла
        input_file = "./output/bonds_filter.csv"
        output_file = "./output/bonds_no_isin.csv"
        
        logging.info(f"Чтение данных из файла {input_file}")
        df = pd.read_csv(input_file, sep=';', encoding='utf-8')
        
        # Поиск облигаций без ISIN
        no_isin_df = df[df['ISIN'].isna() | (df['ISIN'] == '')]
        
        # Сохранение результата
        no_isin_df.to_csv(output_file, sep=';', index=False, encoding='utf-8')
        
        # Логирование результатов
        total_bonds = len(df)
        no_isin_count = len(no_isin_df)
        logging.info(f"Всего облигаций: {total_bonds}")
        logging.info(f"Найдено облигаций без ISIN: {no_isin_count}")
        logging.info(f"Данные сохранены в файл {output_file}")
        
        if no_isin_count > 0:
            logging.info("Список облигаций без ISIN:")
            for _, row in no_isin_df.iterrows():
                logging.info(f"- {row['Название облигации']}")
        
    except Exception as e:
        logging.error(f"Ошибка при обработке данных: {str(e)}")

if __name__ == "__main__":
    logging.info("Запуск скрипта поиска облигаций без ISIN")
    find_bonds_without_isin()
    logging.info("Работа скрипта завершена") 