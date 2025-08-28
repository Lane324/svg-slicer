from typing import cast

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import fsolve

# Inputs
z1 = 4 + 2j  # Start point
z2 = 1 + 5j  # End point
a, b = 3, 2  # Radii
phi = np.radians(30)  # Ellipse rotation
r = a + 1j * b  # Complex radius
N = 10


# Function to solve for center and angles
def ellipse_system(vars):
    xc, yc, t1, t2 = vars
    c = xc + 1j * yc
    exp_phi = np.exp(1j * phi)
    rhs1 = c + r * np.exp(1j * t1) * exp_phi
    rhs2 = c + r * np.exp(1j * t2) * exp_phi
    return [
        np.real(rhs1 - z1),
        np.imag(rhs1 - z1),
        np.real(rhs2 - z2),
        np.imag(rhs2 - z2),
    ]


# Initial guess: center near midpoint, angles 0 and pi/2
mid = (z1 + z2) / 2
initial = [mid.real, mid.imag, 0, np.pi / 2]

solution = fsolve(ellipse_system, initial)
xc, yc, theta1, theta2 = solution

xc = cast(int, xc)
yc = cast(int, yc)

c = xc + 1j * yc

# Generate arc points
if theta2 < theta1:
    theta2 += 2 * np.pi
theta_vals = np.linspace(theta1, theta2, N)
exp_phi = np.exp(1j * phi)
arc_points = c + r * np.exp(1j * theta_vals) * exp_phi
print(type(theta_vals[0]))
print(type(arc_points))
print(type(exp_phi))

# Plot
plt.figure(figsize=(6, 6))
plt.plot(arc_points.real, arc_points.imag, label="Ellipse Arc")
plt.scatter([z1.real, z2.real], [z1.imag, z2.imag], color="red", label="Endpoints")
plt.scatter([c.real], [c.imag], color="blue", label="Center", marker="x")
plt.axis("equal")
plt.grid(True)
plt.title("Ellipse Arc (Complex Representation)")
plt.legend()
plt.show()
