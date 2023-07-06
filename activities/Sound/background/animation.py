import numpy as np
import opensimplex
import qoplots.qoplots as qoplots
qoplots.init("rose_pine", doc_type = "presentation")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

import time

def pinch(y, p = 15):
    # uses a smoothstep function to reduce y to 0 at both ends, only affecting the p% at either end
    n = len(y)
    if p > 1:
        p = p / 100
    # smoothstep function
    def smoothstep(x):
        return 3*x**2 - 2*x**3
    
    # pinch the ends
    for i in range(int(n * p)):
        y[i] *= smoothstep(i / (n * p))
        y[n - i - 1] *= smoothstep(i / (n * p))
    return y

def inverse_smoothstep(x):
    return 0.5 - np.sin(np.arcsin(1 - 2 * x) / 3)

class Wave:

    def __init__(
        self, 
        r,
        x_0 = 0,
        y_0 = 0,
        resolution = 200,
        max_frames = 200,
        speed = 0.05,
        scale = 10,
        detail = 3,
        color = None,
        alpha = 0.5
    ):
        self.r = r / 5
        self.x_0 = x_0
        self.y_0 = y_0
        self.resolution = resolution
        self.max_frames = max_frames
        self.speed = speed
        self.scale = scale
        self.detail = detail
        self.color = color
        self.alpha = alpha
        self.x = np.linspace(0, 1, resolution)
        self.x_offset = np.random.uniform(0, 2)
        self.y_offset = np.random.uniform(0, 2)
        self.theta_offset = np.random.uniform(0, 2 * np.pi)

    def plot(self, ax):
        # produce the initial line to be updated in the update function
        self.line, = ax.plot([], [], lw=1, alpha = self.alpha, color = self.color, ls = "-")
        self.update(0)

    def update(self, frame):
        # update the wave line data
        theta = frame / self.max_frames * 2 * np.pi + self.theta_offset
        y = np.zeros(self.resolution)
        for i in range(self.resolution):
            value = opensimplex.noise3(self.x[i] * self.detail, self.r * np.cos(theta) + self.x_offset, self.r * np.sin(theta) * self.y_offset) * self.scale
            y[i] = value
        y = pinch(y)
        self.line.set_data(self.x, y)
        return self.line,

colors = []
for i, col in enumerate(qoplots.Scheme.accents):
    colors += [c.css for c in col]

# randomly shuffle the colors
np.random.shuffle(colors)

max_frames = 500
N = 100
waves = []
for i in range(N):
    speed = np.abs(np.random.normal(0, 2.5)) # radius of the circle through noise space
    scale = np.abs(5 - speed) * 2 # scale of the wave
    detail = np.random.uniform(3, 15 - scale) # detail of the noise
    waves.append(Wave(speed, scale = scale, detail = detail, max_frames = max_frames, color = colors[i % len(colors)], alpha = 1 - (scale / 10)))

fig = plt.figure()#frameon=False)
fig.set_size_inches(8, 4.5)
ax = plt.Axes(fig, [0., 0., 1., 1.])
ax.set_axis_off()
fig.add_axes(ax)
ax.set_xlim(0, 1)
ax.set_ylim(max([wave.scale for wave in waves]) * -1.1, max([wave.scale for wave in waves]) * 1.1)
for wave in waves:
    wave.plot(ax)

start_time = time.time()

def update(frame):
    # return to the start of the line after printing
    def bar(f, max_f, width = 50):
        completed = int(f / max_f * width)
        return f"[{'=' * completed}{' ' * (width - completed)}]"
    def format_time(remaining):
        if remaining < 60:
            return f"{remaining:.2f}s"
        elif remaining < 3600:
            return f"{remaining / 60:.0f}:{remaining % 60:0>2.0f}"
        else:
            return f"{remaining / 3600:.2f}h"

    current_time = time.time()
    elapsed_time = current_time - start_time
    remaining_time = elapsed_time / (frame + 1) * (max_frames - frame - 1)
    print(f"Frame: {frame: >3d} / {max_frames} {bar(frame, max_frames)} ({frame / max_frames * 100:.2f}%, {format_time(remaining_time)})", end = "\x1b[0G", flush = True)
    for wave in waves:
        wave.update(frame)
    plt.savefig(f"frames/{frame:0>3d}.png", dpi = 320, transparent=False)
    return [wave.line for wave in waves]

# Create the animation
animation = FuncAnimation(fig, update, frames=max_frames, interval=50, blit=False)
animation.save("animation.mp4", fps = 30, dpi = 400)

# Display the animation
# plt.show()
