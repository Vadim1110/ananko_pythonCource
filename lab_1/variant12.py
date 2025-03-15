lst = [
    [0, 0, 0, 0],
    [3, 5, 0, 6],
    [8, 1, -7, 10],
    [0, 0, 0, 0]
]

lst = [row for row in lst if any(row)]
for row in lst:
    print(row)

for i, row in enumerate(lst):
    if any(number > 0 for number in row):
        print()
        break
