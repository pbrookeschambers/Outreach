import numpy as np
import qoplots.qoplots as qoplots
qoplots.init("rose_pine", doc_type = "presentation")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
from fractions import Fraction as Frac

def wave(idx, w, x_max, x):
    x_local = x + x_max * idx
    if idx % 2 == 1:
        x_local = x_local[::-1]
    y = np.sin(2 * np.pi * x_local / w) * (-1) ** (idx)
    return y

color = qoplots.Scheme.accents[0].base.css
fig = plt.figure()
fig.set_size_inches(8, 4.5)
ax = plt.Axes(fig, [0., 0., 1., 1.])
ax.set_axis_off()
fig.add_axes(ax)
ax.set_xlim(0, 1)
ax.set_ylim(-4, 4)

N_data = 2
N_show = 2
max_frames = 2000

plt.axhline(1, color = qoplots.Scheme.foreground[3].css, ls = "--")
plt.axhline(-1, color = qoplots.Scheme.foreground[3].css, ls = "--")

lines = [None] * N_show
total = None 
x_max = 1
x = np.linspace(0, x_max, 300)
a = 1 / (8 * np.pi)
f = 20 * np.pi
t = np.linspace(0, 1, max_frames // 2)
ws = 1/(a * (t * f - np.sin(t * f)) + 0.5)
ws = np.concatenate((ws, ws[::-1]))
y = np.zeros((N_data, len(x)))
for i in range(N_data):
    y[i] = wave(i, ws[0], x_max, x)
    if i < N_show:
        lines[i], = plt.plot(x, y[i] + 1, color = color, lw = 1, alpha = (1-i/N_show), ls = "solid" if i == 0 else ":")

y_total = np.sum(y, axis = 0)
# normalise
y_total = y_total / N_data
total, = plt.plot(x, y_total - 1, lw = 2, alpha = 1, ls = "solid", color = qoplots.Scheme.accents[1].base.css)

textlambda = plt.text(0.825, 2.5, "$\lambda =$", color = qoplots.Scheme.accents[4].base.css, ha = "right", va = "center", fontsize = 20)
text = plt.text(0.9, 2.5, "$2L$", color = qoplots.Scheme.accents[4].base.css, ha = "right", va = "center", fontsize = 20)

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
    

    w = ws[frame]
    frac = Frac(w).limit_denominator(300)
    if frac.denominator == 1:
        text.set_text(f"${frac.numerator if frac.numerator != 1 else ''}L$")
    else:
        text.set_text(f"$\\frac{{{frac.numerator}}}{{{frac.denominator}}}L$")

    y = np.zeros((N_data, len(x)))
    for i in range(N_data):
        y[i] = wave(i, w, x_max, x)
        if i < N_show:
            lines[i].set_data(x, y[i] + 1)

    y_total = np.sum(y, axis = 0)
    # normalise
    y_total = y_total / N_data
    total.set_data(x, y_total - 1)

start_time = time.time()
anim = FuncAnimation(fig, update, frames=np.arange(0, max_frames), interval=20)
anim.save('animation.mp4', fps=30, dpi = 400)
