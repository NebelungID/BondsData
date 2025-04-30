import csv

# Порядок рейтингов от высшего к низшему
RATING_ORDER = {
    'AAA': 1,
    'AA+': 2,
    'AA': 3,
    'AA-': 4,
    'A+': 5,
    'A': 6,
    'A-': 7,
    'BBB+': 8,
    'BBB': 9,
    'BBB-': 10,
    'BB+': 11,
    'BB': 12,
    'BB-': 13,
    'B+': 14,
    'B': 15,
    'B-': 16,
    'CCC': 17,
    'D': 18,
    'Нет данных': 99,
    'Ошибка': 100
}

def get_rating_value(rating):
    return RATING_ORDER.get(rating, 100)

# Чтение данных из файла
with open('output/bonds_with_ratings.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f, delimiter=';')
    header = next(reader)
    rows = list(reader)

# Сортировка по рейтингу
sorted_rows = sorted(rows, key=lambda x: get_rating_value(x[5]))

# Запись отсортированных данных обратно в файл
with open('output/bonds_with_ratings.csv', 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f, delimiter=';')
    writer.writerow(header)
    writer.writerows(sorted_rows)

print("Файл успешно отсортирован по рейтингу") 