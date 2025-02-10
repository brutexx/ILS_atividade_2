
problema = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

a = next((a for a in problema))

a.remove(1)

print(a)
print(problema)