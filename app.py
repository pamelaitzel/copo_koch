# -*- coding: utf-8 -*-
import math
from io import BytesIO
from flask import Flask, request, send_file, render_template, url_for

import matplotlib
matplotlib.use("Agg")  # backend sin GUI
import matplotlib.pyplot as plt

app = Flask(__name__)

# ------------------- LÓGICA DEL FRACTAL -------------------

def koch_curve(order, length=1.0, start=(0.0, 0.0), angle_deg=0.0):
    if order == 0:
        rad = math.radians(angle_deg)
        end = (start[0] + length * math.cos(rad),
               start[1] + length * math.sin(rad))
        return [start, end]
    seg = length / 3.0
    a = start
    rad0 = math.radians(angle_deg)
    b = (a[0] + seg * math.cos(rad0), a[1] + seg * math.sin(rad0))
    c = (b[0] + seg * math.cos(math.radians(angle_deg + 60)),
         b[1] + seg * math.sin(math.radians(angle_deg + 60)))
    d = (c[0] + seg * math.cos(math.radians(angle_deg - 60)),
         c[1] + seg * math.sin(math.radians(angle_deg - 60)))
    e = (d[0] + seg * math.cos(rad0), d[1] + seg * math.sin(rad0))

    pts = []
    pts += koch_curve(order - 1, seg, a, angle_deg)[:-1]
    pts += koch_curve(order - 1, seg, b, angle_deg + 60)[:-1]
    pts += koch_curve(order - 1, seg, c, angle_deg - 60)[:-1]
    pts += koch_curve(order - 1, seg, d, angle_deg)
    return pts

def koch_two_sides(order, length=1.0):
    left_start = (-length / 2.0, 0.0)
    side1 = koch_curve(order, length, left_start, 0.0)
    mid = (0.0, 0.0)
    side2 = koch_curve(order, length, mid, 60.0)
    return side1, side2

def koch_snowflake(order, length=1.0):
    h = (math.sqrt(3) / 2.0) * length
    p1 = (-length / 2.0, 0.0)
    p2 = ( length / 2.0, 0.0)
    p3 = (0.0, h)
    side1 = koch_curve(order, length, p1,   0.0)
    side2 = koch_curve(order, length, p2, 120.0)
    side3 = koch_curve(order, length, p3,-120.0)
    return [side1, side2, side3]

# ------------------- HELPERS -------------------

def _clamp_int(v, vmin, vmax, default):
    try:
        x = int(v)
        return max(vmin, min(vmax, x))
    except Exception:
        return default

def _float_pos(v, default):
    try:
        x = float(v)
        return max(0.1, min(10.0, x))
    except Exception:
        return default

def _hex_color(v, default):
    if isinstance(v, str) and len(v) in (4,7) and v.startswith("#"):
        return v
    return default

def _get_params(args):
    fig = args.get("fig", "curve")
    order = _clamp_int(args.get("order", 4), 0, 7, 4)
    lw = _float_pos(args.get("lw", 1.8), 1.0)
    c1 = _hex_color(args.get("c1", "#67e8f9"), "#67e8f9")
    c2 = _hex_color(args.get("c2", "#f0abfc"), "#f0abfc")
    return {"fig": fig, "order": order, "lw": lw, "c1": c1, "c2": c2}

# ------------------- RUTAS -------------------

@app.route("/")
def index():
    params = _get_params(request.args)
    plot_url = url_for("plot", **params, fmt="png", n=params["order"])
    download_png = url_for("plot", **params, fmt="png", download=1)
    download_svg = url_for("plot", **params, fmt="svg", download=1)
    return render_template("index.html", params=params, plot_url=plot_url,
                           download_png=download_png, download_svg=download_svg)

@app.route("/plot")
def plot():
    params = _get_params(request.args)
    fmt = request.args.get("fmt", "png").lower()
    download = request.args.get("download")

    fig = plt.figure(figsize=(7,6), dpi=150)
    ax = fig.add_subplot(111)
    ax.set_facecolor("#0b1020")
    ax.axis("off")
    ax.set_aspect("equal", adjustable="box")

    order, lw, c1, c2 = params["order"], params["lw"], params["c1"], params["c2"]

    if params["fig"] == "curve":
        pts = koch_curve(order, length=1.0, start=(-0.5, 0.0), angle_deg=0.0)
        x, y = zip(*pts)
        ax.plot(x, y, linewidth=lw, color=c1)
        ax.set_xlim(-0.55, 0.55)
        ax.set_ylim(-0.15, 0.35)

    elif params["fig"] == "two":
        side1, side2 = koch_two_sides(order, length=1.0)
        x1, y1 = zip(*side1); x2, y2 = zip(*side2)
        ax.plot(x1, y1, linewidth=lw, color=c1)
        ax.plot(x2, y2, linewidth=lw, color=c2)
        ax.set_xlim(-0.65, 0.65)
        ax.set_ylim(-0.15, 0.7)

    else:  # snow
        sides = koch_snowflake(order, length=1.0)
        colors = [c1, c2, "#a7f3d0"]
        for i, side in enumerate(sides):
            x, y = zip(*side)
            ax.plot(x, y, linewidth=lw, color=colors[i % len(colors)])
        ax.set_xlim(-0.7, 0.7)
        ax.set_ylim(-0.15, 0.95)

    buf = BytesIO()
    if fmt == "svg":
        fig.savefig(buf, format="svg", bbox_inches="tight")
        mime, ext = "image/svg+xml", "svg"
    else:
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        mime, ext = "image/png", "png"
    plt.close(fig)
    buf.seek(0)

    filename = f"koch_{params['fig']}_o{order}.{ext}"
    return send_file(buf, mimetype=mime, as_attachment=bool(download), download_name=filename)

# ------------------- MAIN -------------------

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
