import pandas as pd
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bonds_transform.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def transform_data():
    try:
        # Чтение исходного файла
        input_file = "./output/bonds_filter.csv"
        output_file = "./output/bonds_transformed.csv"
        
        logging.info(f"Чтение данных из файла {input_file}")
        df = pd.read_csv(input_file, sep=';', encoding='utf-8')
        
        # Создание нового DataFrame с нужными колонками
        new_df = pd.DataFrame({
            'Название облигации': df['Название облигации'],
            'B': 'B',
            'ISIN': df['ISIN'],
            '1': 1,
            '0.01': 0.01
        })
        
        # Сохранение результата
        new_df.to_csv(output_file, sep=';', index=False, encoding='utf-8')
        logging.info(f"Данные успешно преобразованы и сохранены в файл {output_file}")
        logging.info(f"Обработано {len(new_df)} облигаций")
        
    except Exception as e:
        logging.error(f"Ошибка при преобразовании данных: {str(e)}")

if __name__ == "__main__":
    logging.info("Запуск скрипта преобразования данных")
    transform_data()
    logging.info("Работа скрипта завершена") 