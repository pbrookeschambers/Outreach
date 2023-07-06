import numpy as np
import qoplots.qoplots as qoplots
qoplots.init("rose_pine", doc_type = "presentation")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
from fractions import Fraction as Frac

def wave(x, f):
    E = 1
    c = 1
    A = (1/(E * c * f)) ** (1 / 2)
    y = np.sin(2 * np.pi * x * f) * A
    return y



color_point = qoplots.Scheme.accents[0].base.css
color_main = qoplots.Scheme.accents[1].base.css
color = qoplots.Scheme.accents[4].base.css
fig = plt.figure()
fig.set_size_inches(8, 4.5)
ax = plt.Axes(fig, [0., 0., 1., 1.])
ax.set_axis_off()
# mini plot in the top right corner
mini_ax = plt.Axes(fig, [0.7, 0.1, 0.25, 0.25])
fig.add_axes(ax)
fig.add_axes(mini_ax)
ax.set_xlim(0, 1)
ax.set_ylim(-4, 4)

N = 20
E = 1

max_frames = 1500

lines = [None] * N
fading = [False] * N
changing_line = None
x_max = 1
x = np.linspace(0, x_max, 300)
dalpha = 0.05

freq = 1 / (
    2 * np.exp(np.log(1/(N))*np.linspace(0, 1, max_frames))
)
amp = 1 / np.sqrt(freq)
amp = amp / amp[0]

mini_ax.set_xlim(0, max(freq))
mini_ax.set_ylim(0, max(amp))
mini_ax.set_xlabel("Frequency, $f$")
mini_ax.set_ylabel("Amplitude, $A$")
# turn off the axis ticks
mini_ax.tick_params(left = False, right = False , labelleft = False, labelbottom = False, bottom = False)
c = 1
fs = [c/x_max*(i+1)/2 for i in range(N)]
print("\n".join([f"{i+1}: {fs[i]:.2f}" for i in range(N)]) + "\n\n")

for i in range(N):
    lines[i], = ax.plot(x, wave(x, fs[i]), color = color, lw = 1, alpha = 0, ls = "solid")

changing_line, = ax.plot(x, wave(x, fs[0]), color = color_main, lw = 2, alpha = 1, ls = "solid")
changing_line_2, = ax.plot(x, wave(x, fs[0]), color = color_point, lw = 2, alpha = 1, ls = "solid")
# point = plt.scatter([x_max], [0], color = color_point, s = 30, alpha = 1, marker = 'o')
mini_line, = mini_ax.plot([0], [0], color = color_main, lw = 2, alpha = 1, ls = "solid")
# mini_point = mini_ax.scatter([0], [0], color = color, s = 30, alpha = 1, marker = 'o')

f_idx = 0
def update(frame):
    global f_idx
    try:
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
        
        # lerp between 2 and 2/N by frame/max_frames
        w = 2 * np.exp(np.log(1/(N))*frame / max_frames)
        f = 1 / w
        # f = 0.5 + frame / max_frames * (N / 2 - 1)
        print(f"\nFrequency: {f:.2f} Hz. f_idx: {f_idx} \x1b[1F", end = "", flush = True)
        if f > fs[f_idx]:
            print(f"\n\nReached {f_idx+1} of {N} frequencies. \x1b[2F", end = "", flush = True)
            lines[f_idx].set_alpha(0.5 * (1 - f_idx / (N+1)))
            # lines[f_idx].set_alpha(1)
            fading[f_idx] = True
            f_idx += 1
        
        # for fade, line in zip(fading, lines):
        #     if fade:
        #         line.set_alpha(max(line.get_alpha() - dalpha, 0))
        #         if line.get_alpha() <= 0:
        #             line.set_alpha(0)
        #             fading[fading.index(fade)] = False

        y = wave(x, f)
        changing_line.set_ydata(y)
        changing_line_2.set_ydata(y)
        if abs(y[-1]) / np.max(y) <= 5e-2:
            # point.set_alpha(1)
            # changing_line.set_color(color_point)
            changing_line_2.set_alpha(1)
        else:
            # point.set_alpha(0)
            # changing_line.set_color(color_main)
            changing_line_2.set_alpha(max(0, changing_line_2.get_alpha() - dalpha))
        mini_line.set_data(freq[:frame], amp[:frame])
        # mini_point.set_offsets([freq[frame], amp[frame]])
    except:
        print("\n\n\n")
        raise
    return lines + [changing_line]#, point]


start_time = time.time()
anim = FuncAnimation(fig, update, frames=np.arange(0, max_frames), interval=20)
anim.save('animation.mp4', fps=30, dpi = 400)
