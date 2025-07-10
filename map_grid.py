import numpy as np

def generate_offsets_grid(size, precision, spacing):
    coordinates = []
    
    array_1 = np.arange(0, size*spacing-spacing, spacing)
    array_2 = np.arange(0, size*spacing-spacing, spacing)

    correction = spacing*(size//2)

    for i in range(len(array_1)):
        for t in range(len(array_2)):

            one = array_1[i]
            one = one - correction
            two = array_2[t]
            two = two - correction

            #print(array_2[t])
            #coordinates.append([round(array_1[i], precision), round(array_2[t])])
            coordinates.append([one, two])

        array_2 = array_2[::-1]
    return coordinates

size = 3
precision = 2
spacing = 0.1
coords = generate_offsets_grid(size, precision, spacing)
print(coords)