import numpy as np

import qoplots.qoplots as qoplots
qoplots.init("rose_pine")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def initial(x, t):
    c = 2
    wavelength = 0.05
    # return np.exp(-((x - c * t) / wavelength) ** 2 / 2) * np.cos(2 * np.pi * x / wavelength - 2 * np.pi * c * t / wavelength)
    # gaussian at c * t, with sigma = wavelength / 2
    return (np.exp(-((x - c * t) / (wavelength / 2)) ** 2 / 2))

def init():
  x = np.linspace(0,1,500)
  t = np.linspace(0,1,500)
  dx = x[1] - x[0]
  dt = t[1] - t[0]

  c = 2
  C = c * dt / dx / 10 # we'll do 10 steps per frame
  C2 = C**2

  # initial conditions
  u_1 = initial(x, t = 0.25)
  u = initial(x, t = 0.25 + dt / 10)
  u[0] = 0
  u[-1] = 0

  u_2, u_1 = u_1, u
  return x, t, u_1, u_2, C2

def step(u_1, u_2, C2):
    u = 2 * u_1 - u_2 + C2 * (np.roll(u_1,1) - 2 * u_1 + np.roll(u_1,-1))
    u[0] = 0
    u[-1] = 0
    u_2, u_1 = u_1, u
    return u_1, u_2

def update(frame):
    global line, C2, x, u_1, u_2
    print(f"Frame: {frame: >3d}", end = "\x1b[0G", flush = True)
    for i in range(10):
      u_1, u_2 = step(u_1, u_2, C2)
    line.set_data(x, u_1)
    return line,

line = None
C2 = None
x = None
u_1 = None
u_2 = None

def main():
  global line, C2, x, u_1, u_2
  x, t, u_1, u_2, C2 = init()

  # set up the figure
  fig = plt.figure()
  fig.set_size_inches(8, 4.5)
  ax = plt.Axes(fig, [0., 0., 1., 1.])
  ax.set_axis_off()
  fig.add_axes(ax)
  ax.set_xlim(0, 1)
  ax.set_ylim(-2, 2)


  line, = ax.plot([], [], lw=1)
  line.set_data(x, u_1)

  max_frames = len(t)

  anim = FuncAnimation(fig, update, frames=np.arange(0, max_frames), interval=20)
  anim.save('animation.mp4', fps=30, dpi = 400)

if __name__ == "__main__":
  main()