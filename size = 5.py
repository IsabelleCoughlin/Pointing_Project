points = 3
pres_num = 0.1

coordinates = []
x = 0.0
y = 0.0
coordinates.append([x, y]) 

t = 1 #current side length

directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
dir_idx = 0 # Cue for time to change directions

while len(coordinates) < points**2:
    dx, dy = directions[dir_idx % 4]

    for z in range(0, t):
        x = x + (pres_num*dx)
        y = y + (pres_num*dy)
        coordinates.append([x, y])
        if len(coordinates) == points**2:
            break
    
    dir_idx += 1
    if(dir_idx % 2) == 0:
        t += 1



    

print(coordinates)