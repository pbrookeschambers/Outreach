import numpy as np
import qoplots.qoplots as qoplots
qoplots.init("rose_pine")
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
ax.set_ylim(-2, 2)

x = np.linspace(0, 1, 500)
f = 3
y = np.sin(2 * np.pi * f * x)

line, = ax.plot([], [], lw=1)
line.set_data(x, y)

max_frames = 100

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
    
    phase = frame / max_frames * 2 * np.pi
    y = np.sin(2 * np.pi * f * x - phase)
    line.set_data(x, y)
    plt.savefig(f"frames/{frame:0>3d}.png")
    return line,

anim = FuncAnimation(fig, update, frames=np.arange(0, max_frames), interval=20)
anim.save('animation.mp4', fps=30, dpi = 400)
