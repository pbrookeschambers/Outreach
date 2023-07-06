import numpy as np
import qoplots.qoplots as qoplots
qoplots.init("rose_pine", doc_type = "presentation")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time

# simple animation of a travelling wave

# set up the figure
fig = plt.figure()
fig.set_size_inches(8, 4.5)
ax = plt.Axes(fig, [0., 0., 1., 1.])
ax.set_axis_off()
fig.add_axes(ax)
ax.set_xlim(0, 1)
ax.set_ylim(-4, 4)

x = np.linspace(0, 1, 1000)
f = 3
y = np.sin(2 * np.pi * f * x)

lines = [None, None, None]
lines[0], = ax.plot([], [], lw=1, alpha = 0.5)
lines[0].set_data(x, y)
lines[1], = ax.plot([], [], lw=1, alpha = 0.5)
lines[1].set_data(x, y)
lines[2], = ax.plot([], [], lw=1)
lines[2].set_data(x, y)

max_frames = 500

start_time = time.time()

def wave(x, wavelength, c, t):
    # non-dispersive wavepacket (real part)
    # return np.exp(-((x - c * t) / wavelength) ** 2 / 2) * np.cos(2 * np.pi * x / wavelength - 2 * np.pi * c * t / wavelength)

    # gaussian at c * t, with sigma = wavelength / 2
    return (np.exp(-((x - c * t) / (wavelength / 2)) ** 2 / 2))

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
    
    w = 0.08
    y1 = wave(x, w, 1, frame / max_frames)
    # y2 starts from the right and propagates to the left
    y2 = -wave(x, w, 1, (1 - frame / max_frames))
    lines[0].set_data(x, y1 + 2)
    lines[1].set_data(x, y2)
    y = y1 + y2
    lines[2].set_data(x, y - 2)
    # plt.savefig(f"frames/{frame:0>3d}.png")
    return lines

anim = FuncAnimation(fig, update, frames=np.arange(0, max_frames), interval=20)
anim.save('animation.mp4', fps=30, dpi = 400)
