# Initialize variables
boo = True
positive = True
x_turn = True

x = 0.0
y = 0.0

coordinates = []  # Define the list to store coordinates
coordinates.append([0.0, 0.0])  # Start with the origin

t = 1
pres_num = 0.1  # Step size for movement
points = 3  # Number of points per side (e.g., 5x5 grid)

while boo:
    area = len(coordinates)

    if positive:
        if x_turn:
            for z in range(0, t):
                x = x + pres_num
                coordinates.append([x, y])
            x_turn = False
        else:
            for z in range(0, t):
                y = y + pres_num
                coordinates.append([x, y])
            x_turn = True
        positive = False
    else:
        if x_turn:
            for z in range(0, t):
                x = x - pres_num
                coordinates.append([x, y])
            x_turn = False
        else:
            for z in range(0, t):
                y = y - pres_num
                coordinates.append([x, y])
            x_turn = True
        positive = True

    # Stop the loop when the number of points reaches points^2
    if area >= points**2:
        boo = False

    t = t + 1

print(coordinates)