"""Build the README figures from the pipeline step images and labeled results."""
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.image import imread

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "docs" / "figures"
BG, FG = "#0d1117", "#e6edf3"
plt.rcParams.update({"figure.facecolor": BG, "savefig.facecolor": BG, "text.color": FG})


def grid(images, titles, out, cols, size):
    rows = (len(images) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=size)
    for ax in axes.flat:
        ax.axis("off")
    for ax, img, t in zip(axes.flat, images, titles):
        ax.imshow(imread(img), cmap="gray")
        ax.set_title(t, fontsize=13, color=FG, pad=8)
    fig.tight_layout()
    fig.savefig(FIG / out, dpi=110)
    plt.close(fig)


steps = sorted(FIG.glob("step_*.jpg"))
grid(steps, ["1 · Input ballot", "2 · Gaussian blur", "3 · Inverse threshold",
             "4 · External contours", "5 · Square filter (area, aspect, 4 vertices)", "6 · Fill / tick classification"],
     "pipeline.png", 3, (15, 11))

labeled = [ROOT / "results" / f"{n}_labeled.jpg" for n in ("vote1", "vote4", "vote5", "vote6")]
grid(labeled, ["#002 · valid", "#004 · valid", "R005 · too many inspectors", "R006 · duplicate image"],
     "results.png", 2, (13, 11))
