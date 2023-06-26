import numpy as np

import qoplots.qoplots as qoplots
qoplots.init("rose_pine")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# def initial(x, t):
#     c = 2
#     wavelength = 0.05
#     # return np.exp(-((x - c * t) / wavelength) ** 2 / 2) * np.cos(2 * np.pi * x / wavelength - 2 * np.pi * c * t / wavelength)
#     # gaussian at c * t, with sigma = wavelength / 2
#     # return (np.exp(-((x - c * t) / (wavelength / 2)) ** 2 / 2))
#     return np.zeros_like(x)

# def init():
#   x = np.linspace(0,1,500)
#   t = np.linspace(0,2,1000)
#   dx = x[1] - x[0]
#   dt = t[1] - t[0]

#   c = 2
#   C = c * dt / dx / 10 # we'll do 10 steps per frame
#   C2 = C**2

#   # initial conditions
#   u_1 = initial(x, t = 0.25)
#   u = initial(x, t = 0.25 + dt / 10)
#   u[0] = 0
#   u[-1] = 0

#   u_2, u_1 = u_1, u
#   print(c, C2, "\n\n")

#   return x, t, u_1, u_2, C2

# def step(u_1, u_2, C2, t):
#     u = 2 * u_1 - u_2 + C2 * (np.roll(u_1,1) - 2 * u_1 + np.roll(u_1,-1))
#     # u[0] = 0
#     u[0] = np.sin(t * 2 * np.pi / C2)
#     u[-1] = 0
#     u_2, u_1 = u_1, u
#     return u_1, u_2

# def update(frame):
#     global line, C2, x, u_1, u_2, t
#     print(f"Frame: {frame: >3d}", end = "\x1b[0G", flush = True)
#     t0 = t[frame]
#     dt = t[1] - t[0]
#     for i in range(10):
#       u_1, u_2 = step(u_1, u_2, C2, t0 + i * dt / 10)
#     line.set_data(x, u_1)
#     return line,


# set up the figure
fig = plt.figure()
fig.set_size_inches(8, 4.5)
ax = plt.Axes(fig, [0., 0., 1., 1.])
ax.set_axis_off()
fig.add_axes(ax)
ax.set_xlim(0, 1)
ax.set_ylim(-2, 2)

x = np.linspace(0,1,500)
f = 4
c = 5
u_1 = np.sin(x * 2 * np.pi * f)
u_2 = np.sin(x * 2 * np.pi * f)
u = u_1 + u_2

lines = [None, None, None]
lines[0], = ax.plot([], [], lw=1)
lines[0].set_data(x, u_1)
lines[1], = ax.plot([], [], lw=1)
lines[1].set_data(x, u_2)
lines[2], = ax.plot([], [], lw=1)
lines[2].set_data(x, u)

def update(frames):
    u_1 = np.sin(x * 2 * np.pi * f +  frames / max_frames * c)
    u_1[x + frames / max_frames * c / (2 * np.pi) > c] = 0
    u_2 = np.sin(x * 2 * np.pi * f -  frames / max_frames * c)
    u = u_1 + u_2
    lines[0].set_data(x, u_1)
    lines[1].set_data(x, u_2)
    lines[2].set_data(x, u)
    return lines
    

max_frames = 100

anim = FuncAnimation(fig, update, frames=np.arange(0, max_frames), interval=20)
anim.save('animation.mp4', fps=30, dpi = 400)
