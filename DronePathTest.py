import numpy as np
from scipy.optimize import root
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

def compute_heading_vectors(points):
    headings = []

    for i in range(len(points)-1):
        d = points[i+1] - points[i]
        headings.append(d / np.linalg.norm(d))

    headings.append(headings[-1])

    return headings

def turning_radius(phi, va, load_factor, g = 9.81):
    return va**2 / (g * (-np.sin(phi) + np.sqrt(load_factor**2 + np.sin(phi)**2 - 1.0)))

def residual(
    x,
    X0,
    Xf,
    v1,
    v2,
    va,
    nmax
):
    x = x / np.linalg.norm(x)

    gamma1 = np.arccos(
        np.clip(v1 @ x, -1.0, 1.0)
    )

    gamma2 = np.arccos(
        np.clip(v2 @ x, -1.0, 1.0)
    )

    U1 = np.cross(x, v1)

    u1 = U1 / np.linalg.norm(U1)

    phi1 = np.arccos(
        np.clip(u1[2], -1.0, 1.0)
    )

    r1 = turning_radius(phi1, va, nmax)

    U2 = np.cross(x, v2)

    u2 = U2 / np.linalg.norm(U2)

    phi2 = np.arccos(
        np.clip(u2[2], -1.0, 1.0)
    )

    r2 = turning_radius(phi2, va, nmax)

    rhs = Xf - X0 - r1 * np.tan(gamma1/2) * (x + v1) - r2 * np.tan(gamma2/2) * (x + v2)

    lam = rhs @ x

    lhs = lam * x

    return lhs - rhs

waypoints = [
    ("Warsaw",   52.2297, 21.0122, 120),
    ("Gdansk",   54.3520, 18.6466, 120),
    ("Szczecin", 53.4285, 14.5528, 120),
    ("Berlin",   52.5200, 13.4050, 120),
]

va = 15.0      # m/s
nmax = 1.2002
g = 9.81

X0 = np.array([0.0, 0.0, 0.0])
v1 = np.array([1.0, 1.0, 1.0])/np.sqrt(3)
Xf = np.array([300.0, 400.0, 500.0])
v2 = np.array([1.0, 1.0, 1.0])/np.sqrt(3)

guess = Xf - X0
guess /= np.linalg.norm(guess)

sol = root(
    residual,
    guess,
    args=(
        X0,
        Xf,
        v1,
        v2,
        va,
        nmax
    )
)

x = sol.x
x /= np.linalg.norm(x)

gamma1 = np.arccos(v1 @ x)
gamma2 = np.arccos(v2 @ x)

U1 = np.cross(x, v1)
U2 = np.cross(x, v2)

u1 = U1 / np.linalg.norm(U1)
u2 = U2 / np.linalg.norm(U2)

phi1 = np.arccos(u1[2])
phi2 = np.arccos(u2[2])

r1 = turning_radius(phi1, va, nmax)
r2 = turning_radius(phi2, va, nmax)

W1 = np.cross(v1, U1)
W2 = np.cross(v2, U2)

w1 = W1 / np.linalg.norm(W1)
w2 = W2 / np.linalg.norm(W2)

O1 = X0 + r1*w1
O2 = Xf + r2*w2

Y1 = np.cross(x, U1)
Y2 = np.cross(x, U2)

y1 = Y1 / np.linalg.norm(Y1)
y2 = Y2 / np.linalg.norm(Y2)

P1 = O1 - r1*y1
P2 = O2 - r2*y2

length = (
    r1*gamma1
    +
    np.linalg.norm(P2-P1)
    +
    r2*gamma2
)

import matplotlib.pyplot as plt

t_vals = np.linspace(0, 1, 50)

# Łuk 1 (Arc 1): od X0 do P1 za pomocą interpolacji sferycznej (SLERP)
vec_start1 = X0 - O1
vec_end1 = P1 - O1
arc1 = np.array([
    O1 + (np.sin((1 - t) * gamma1) / np.sin(gamma1)) * vec_start1 + 
         (np.sin(t * gamma1) / np.sin(gamma1)) * vec_end1 
    for t in t_vals
])

# Łuk 2 (Arc 2): od P2 do Xf za pomocą interpolacji sferycznej (SLERP)
vec_start2 = P2 - O2
vec_end2 = Xf - O2
arc2 = np.array([
    O2 + (np.sin((1 - t) * gamma2) / np.sin(gamma2)) * vec_start2 + 
         (np.sin(t * gamma2) / np.sin(gamma2)) * vec_end2 
    for t in t_vals
])

# 3. Konfiguracja wykresu 3D
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Rysowanie poszczególnych segmentów
ax.plot(arc1[:, 0], arc1[:, 1], arc1[:, 2], 'r-', linewidth=2.5, label='Zakręt początkowy')
ax.plot([P1[0], P2[0]], [P1[1], P2[1]], [P1[2], P2[2]], 'g-', linewidth=2.5, label='Lot prostoliniowy')
ax.plot(arc2[:, 0], arc2[:, 1], arc2[:, 2], 'b-', linewidth=2.5, label='Zakręt końcowy')

# Zaznaczenie punktów kluczowych
ax.scatter(*X0, color='black', s=60, label='X0 (Start)', zorder=5)
ax.scatter(*Xf, color='black', s=60, label='Xf (Koniec)', zorder=5)
ax.scatter(*P1, color='orange', s=40, label='P1 (Koniec zakrętu 1)')
ax.scatter(*P2, color='purple', s=40, label='P2 (Początek zakrętu 2)')

# Opisy osi i legenda
ax.set_xlabel('Oś X [m]')
ax.set_ylabel('Oś Y [m]')
ax.set_zlabel('Oś Z [m]')
ax.set_title('Wizualizacja Trajektorii Lotu Drona 3D')
ax.legend()

# Wyświetlenie wykresu
plt.tight_layout()
plt.show()