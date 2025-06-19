def generate_coordinates(size):
    coordinates = []
    for x in range(-size // 2 + 1, size // 2 + 1):
        for y in range(-size // 2 + 1, size // 2 + 1):
            coordinates.append([x, y])
    return coordinates

grid_size = 3
result = generate_coordinates(grid_size)
#print(result)

# How to access them
#for coord in result:
 #   print(coord[0])
#    print(coord[1])