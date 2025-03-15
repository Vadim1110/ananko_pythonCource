def count_max(row):
    max_count = 0
    for num in row:
        max_count = max(max_count, row.count(num))
    return max_count


def sort_count(lst):
    return sorted(lst, key=count_max)


lst = [
    [-3, 3, -1, 0],
    [3, 5, 5, 5],
    [8, 1, -7, 10],
    [6, 5, 1, 9]
]

sorted_lst = sort_count(lst)

for row in sorted_lst:
    print(row)

for col in range(len(lst[0])):
    if all(row[col] >= 0 for row in lst):
        print("Номер первого столбца без отрицательных элементов:", col + 1)
        break
else:
    print("Нет столбцов без отрицательных элементов")

