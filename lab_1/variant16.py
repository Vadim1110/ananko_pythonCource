lst = [
    [-3, -4, -1, 1],
    [3, 5, 5, 5],
    [8, 1, -7, 1],
    [6, 5, 5, 9]
]

def count_max(row):
    max_count = 0
    for num in row:
        max_count = max(max_count, row.count(num))
    return max_count

sorted_lst = sorted(lst, key=count_max)

for row in sorted_lst:
    print(row)

for col in range(len(lst[0])):
    if all(row[col] >= 0 for row in lst):
        print(col + 1)
        break
