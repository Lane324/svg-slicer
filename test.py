import math

import numpy

start = 1 + 2j
end = 3 + 4j
radius = 3 + 2j

distance = math.dist((start.real, start.imag), (end.real, end.imag))
midpoint = (end + start) / 2
normal = complex((end.real - start.real) / distance, (end.imag - start.imag) / distance)
midpoint_to_center = math.sqrt(radius**2 - distance**2 / 4)
center = complex(
    (start.real + end.real) / 2 - midpoint_to_center * normal.real,
    (start.imag + end.imag) / 2 + midpoint_to_center * normal.imag,
)

theta1 = math.atan2(start.imag - center.imag, start.real - center.real)
theta2 = math.atan2(end.imag - center.imag, end.real - center.real)


points = []

for t in numpy.linspace(0, 1, 9999):
    x = center.real + radius * math.cos(theta1 + t * (theta2 - theta1))
    y = center.imag + radius * math.sin(theta1 + t * (theta2 - theta1))
    points.append((x, y))


print(f"{distance=}")
print(f"{midpoint=}")
print(f"{normal=}")
print(f"{midpoint_to_center=}")
print(f"{center=}")
print(f"{theta1=}")
print(f"{theta2=}")
print(f"{points[1:-1]=}")
