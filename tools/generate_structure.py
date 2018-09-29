

sections = 2
width = 2000
height = 2000
element_length = 3000

coordinates = []
elements = []
_girder_per_section = 3


index = 0
for i in range(sections):
    index = i * _girder_per_section
    coordinates.append([float(i * element_length), 0., 0.])
    coordinates.append([float(i * element_length), float(width), 0.])
    coordinates.append([float((i + 0.5) * element_length), float(width / 2), float(height)])
    elements.append([index + 0, index + 3])
    elements.append([index + 1, index + 4])

    elements.append([index + 0, index + 1])

    elements.append([index + 0, index + 2])
    elements.append([index + 1, index + 2])
    elements.append([index + 2, index + 3])
    elements.append([index + 2, index + 4])

    if i > 0:
        elements.append([index - _girder_per_section + 2, index + 2])

index += _girder_per_section
coordinates.append([float((i + 1) * element_length), 0., 0.])
coordinates.append([float((i + 1) * element_length), float(width), 0.])
elements.append([index + 0, index + 1])

coordinate_print = ""
for coordinate in coordinates:
    coordinate_print += "%.1f, %.1f, %.1f |" % (coordinate[0], coordinate[1], coordinate[2])

element_print = ""
for element in elements:
    element_print += "%i, %i |" % (element[0], element[1])

print("\nELEMENTS")
print(element_print)

print("\nCOORDINATES")
print(coordinate_print)

print("\nCROSS-SECTIONS")
print([36 for i in range(len(elements))])

print("\nMATERIALS")
print([1800 for i in range(len(elements))])

print("\nSUPPORTS")

print("\n\nEOF")
