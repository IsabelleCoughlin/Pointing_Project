points = 5
pres_num = 0.1
coordinates = []

x, y = 0.0, 0.0
coordinates.append([x, y])

t = 1  # current side length
directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # right, up, left, down
dir_idx = 0  # direction index

while len(coordinates) < points**2:
    dx, dy = directions[dir_idx % 4]
    
    for _ in range(t):
        x = round(x + dx * pres_num, 10)
        y = round(y + dy * pres_num, 10)
        coordinates.append([x, y])
        if len(coordinates) == points**2:
            break

    dir_idx += 1
    # increase t every two directions (after one full side pair)
    if dir_idx % 2 == 0:
        t += 1

print(coordinates)
