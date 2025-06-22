points = 3
pres_num = 0.1

size = int(points / 2)*pres_num

coordinates = []

#def float_range(start, stop, step):
#    while start < stop:
#        yield round(start, 10)  # Avoid floating-point precision issues
#        start += step

#for x in float_range(-size, size + pres_num, pres_num):
#    for y in float_range(-size, size + pres_num, pres_num):
#        coordinates.append([x, y])

boo = True
positive = True
x_turn = True

x = 0.0
y = 0.0

coordinates.append([0.0,0.0]) 

t = 1
ree = 0

while boo:
    ree = ree + 1
    area = len(coordinates)
    if positive:
        if x_turn:
            for z in range(0, t):
                x = x + pres_num
                coordinates.append([x, y])
                if len(coordinates) == points**2:
                    boo = False
                    break
            x_turn = False
        else:
            for z in range(0, t):
                y = y + pres_num
                coordinates.append([x, y])
                if len(coordinates) == points**2:
                    boo = False
                    break
            x_turn = True
        positive = False
    else:
        if x_turn:
            for z in range(0, t):
                x = x - pres_num
                coordinates.append([x, y])
                if len(coordinates) == points**2:
                    boo = False
                    break
            x_turn = False
        else:
            for z in range(0, t):
                y = y - pres_num
                coordinates.append([x, y])
                if len(coordinates) == points**2:
                    boo = False
                    break
            x_turn = True
        positive = True

    if ree%2 == 0:
        t = t+1

    

print(coordinates)