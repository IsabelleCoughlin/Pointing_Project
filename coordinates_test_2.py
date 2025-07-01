
coordinates = []
x = 0
y = 0
coordinates.append([x, y]) 
spacing = 1
size = 5

t = 1 #current side length

directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
dir_idx = 0 # Cue for time to change directions

while len(coordinates) < size**2: # Square shaped grid
    dx, dy = directions[dir_idx % 4] 

    for z in range(0, t):
        x = x + (spacing*dx)
        y = y + (spacing*dy)
        coordinates.append([x, y])
        if len(coordinates) == size**2: 
            break
    
    dir_idx += 1
    if(dir_idx % 2) == 0: # Every other increase change directions
        t += 1
print(coordinates)