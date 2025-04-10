from collections import defaultdict

x = 0
lst = [
    [0, 2, 2, 8],
    [3, 5, 1, 6],
    [8, 1, -7, 10],
    [1, 1, 0, 1]
]

find_null = [row for row in lst if 0 in row]
print(len(find_null))

max_count = 0
row_index = None

for i, row in enumerate(lst):
    my_dict = defaultdict(int) # default dict
    for num in row:
        my_dict[num] += 1

    max_row_count = max(my_dict.values())

    if max_row_count > max_count:
        max_count = max_row_count
        row_index = i

print(row_index + 1)
