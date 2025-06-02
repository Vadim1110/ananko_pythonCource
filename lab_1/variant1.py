x = 0
lst = [
    [1, 2, 5, 6, ],
    [3, 5, 0, 6, ],
    [8, 1, 7, 10]
]

for row in lst:
    if 0 not in row:
        x += 1

max_value = float('-inf')
for row in lst:
    for number in row:
        if number > max_value:
            max_value = number

print('lines without 0: ' + str(x), '| max number: ' + str(max_value))
