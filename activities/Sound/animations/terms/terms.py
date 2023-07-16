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
ax.set_ylim(-2, 2)

x = np.linspace(0, 1, 500)
f = 6
y = np.sin(2 * np.pi * f * x)

vline_xi = int(len(x) * 0.75)
vline_x = x[vline_xi]
vline = plt.axvline(vline_x, color = qoplots.Scheme.accents[4][5].css, lw = 10)

line, = ax.plot([], [], lw=1)
line.set_data(x, y)
point, = ax.plot([0], [0], ms=10, marker='o', color=qoplots.Scheme.accents[5].base.css, linestyle='None')
# point will track the first peak of the wave
pstart = -1/f * 3/4
px = pstart
py = np.sin(2 * np.pi * f * px) # 1
point.set_data([px], [py])
arrow = plt.arrow(px, py, 0.05, 0, color = qoplots.Scheme.accents[5].base.css, head_width = 0.05, head_length = 0.01)
text = plt.text(px, py+0.1, "Speed, $c$", color = qoplots.Scheme.accents[5].base.css)
freq_text = plt.text(vline_x - 0.035, 0.75, "Frequency, $f$", color = qoplots.Scheme.accents[4].base.css, rotation = "vertical")
max_frames = 200
speed = 1/25

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
    
    phase = frame * speed * 2 * np.pi
    px = pstart + frame * speed / f
    py = 1 # should always be 1
    y = np.sin(2 * np.pi * f * x - phase)
    line.set_data(x, y)
    if frame == 0:
        plt.savefig(f"frames/{frame:0>3d}.png")
    point.set_data([px], [py])
    arrow.set_data(x = px, y = py)
    text.set_position([px, py + 0.1])
    if y[vline_xi] > 0.9:
        vline.set_color(qoplots.Scheme.accents[4].base.css)
    else:
        vline.set_color(qoplots.Scheme.accents[4][5].css)
    return line, point, text, vline

anim = FuncAnimation(fig, update, frames=np.arange(0, max_frames - 1), interval=20)
anim.save('animation.mp4', fps=30, dpi = 400)
