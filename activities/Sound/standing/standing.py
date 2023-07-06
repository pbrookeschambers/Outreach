import numpy as np
import qoplots.qoplots as qoplots
qoplots.init("rose_pine", doc_type = "presentation")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time

def smoothstep(x, start, end, reverse = False):
    if x < start:
        v = 0
    elif x > end:
        v = 1
    else:
        x_tmp = (x - start) / (end - start)
        v = 3 * x_tmp ** 2 - 2 * x_tmp ** 3
    if reverse:
        return 1 - v
    else:
        return v


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
node_idx = int(len(x) / 2.5 / 2)
antinode_idx = int(len(x) * 0.5)
f = 3
y = np.sin(2 * np.pi * f * x)

lines = [None, None, None, None]
lines[0], = ax.plot([], [], lw=1, alpha = 0.5)
lines[0].set_data(x, y)
lines[1], = ax.plot([], [], lw=1, alpha = 0.5)
lines[1].set_data(x, y)
lines[2], = ax.plot([], [], lw=1)
lines[2].set_data(x, y)
lines[3], = ax.plot([], [], lw=1, marker = "x", ls = ":", color = qoplots.Scheme.accents[3].base.css, alpha = 0)
lines[3].set_data(x, y)
node, = ax.plot([x[node_idx]], [-1], marker = "x", ls = "none", color = qoplots.Scheme.accents[3].base.css, alpha = 0)
antinode, = ax.plot([x[antinode_idx], x[antinode_idx]], [2, 0], marker = "x", ls = "none", color = qoplots.Scheme.accents[3].base.css, alpha = 0)

max_frames = 1000

start_time = time.time()

def wave(x, wavelength, c, t):
    return np.sin(2 * np.pi * x / wavelength - 2 * np.pi * c * t / wavelength) * 0.5

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
    
    w = (max(x) - min(x)) / 2.5
    c = 0.004
    y1 = wave(x, w, c, frame)
    # y2 starts from the right and propagates to the left
    y2 = wave(x, w, c, (max_frames - frame))
    lines[0].set_data(x, y1 + 1)
    lines[1].set_data(x, y2 + 1)
    y = y1 + y2
    lines[2].set_data(x, y - 1)
    lines[3].set_data([x[node_idx]]*3, [y1[node_idx] + 1, 1, y2[node_idx] + 1])
    lines[3].set_alpha(smoothstep(frame / max_frames, 0.1, 0.15) * smoothstep(frame / max_frames, 0.45, 0.5, reverse = True))
    node.set_alpha(smoothstep(frame / max_frames, 0.1, 0.15) * smoothstep(frame / max_frames, 0.45, 0.5, reverse = True))
    antinode.set_data([x[antinode_idx], x[antinode_idx]], [y1[antinode_idx] + 1, y[antinode_idx] - 1])
    antinode.set_alpha(smoothstep(frame / max_frames, 0.5, 0.55) * smoothstep(frame / max_frames, 0.85, 0.9, reverse = True))
    # plt.savefig(f"frames/{frame:0>3d}.png")
    return lines

anim = FuncAnimation(fig, update, frames=np.arange(0, max_frames), interval=20)
anim.save('animation.mp4', fps=30, dpi = 400)
