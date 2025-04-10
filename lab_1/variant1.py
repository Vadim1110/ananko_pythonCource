x = 0
lst = [
    [1, 2, 5, 6, ],
    [3, 5, 0, 6, ],
    [8, 1, 7, 10]
]

find_null = [row for row in lst if 0 not in row]

max_value = float('-inf')
for row in lst:
    for number in row:
        max_value = max(max_value, number) #add max()

print(len(find_null) ,max_value)
