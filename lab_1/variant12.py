import pprint

lst = [
    [0, 0, 0, 0],
    [-3, -5, 0, -6],
    [8, 1, 7, 10],
    [0, 0, 0, 0],
    [0, -4, 6, -5]
]

full_row = [row for row in lst if any(row)]

for row in full_row:
    pprint.pprint(row)

for i, row in enumerate(lst):
    if any(number > 0 for number in row):
        print(i)
        break
