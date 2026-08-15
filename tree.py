import random
from functools import partial

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider
from matplotlib.patches import Circle, FancyArrowPatch
from matplotlib.animation import FuncAnimation

from fredde import freddies


# ============================================================
#  ВИЗУАЛЬНЫЕ НАСТРОЙКИ (тёмная тема в стиле Obsidian)
# ============================================================
BG_COLOR       = "#202225"   # фон окна и осей
PANEL_COLOR    = "#2b2d31"   # фон панели настроек / кнопок
PANEL_HOVER    = "#3b3d42"
EDGE_COLOR     = "#5a5d63"   # цвет связей родитель -> ребёнок
TEXT_COLOR     = "#dcddde"   # цвет имени узла
GEN_TEXT_COLOR = "#75787f"   # цвет подписи поколения под узлом
ACCENT_COLOR   = "#7289da"   # обводка узла при перетаскивании / акцент слайдеров

NODE_RADIUS = 0.16

# ============================================================
#  ФИЗИКА (аналог "force graph" в Obsidian), регулируется ползунками.
#  gen_pull специально слабый: поколения задают лишь лёгкий вертикальный
#  дрейф, а не жёсткие ряды — иначе граф превращается в застывшее дерево.
# ============================================================
DEFAULT_PARAMS = {
    "repulsion":   1.15,
    "spring_len":  1.9,
    "spring_k":    0.03,
    "gen_pull":    0.015,
    "center_pull": 0.004,
    "damping":     0.86,
    "jitter":      0.010,
    "dt":          0.7,
}

SLIDERS = [
    # (ключ,          подпись,                  min,   max)
    ("repulsion",     "Отталкивание узлов",     0.1,   3.0),
    ("spring_len",    "Длина связи",            0.5,   4.0),
    ("spring_k",      "Жёсткость связи",        0.0,   0.12),
    ("gen_pull",      "Тяга к поколению",       0.0,   0.15),
    ("center_pull",   "Тяга к центру",          0.0,   0.02),
    ("damping",       "Затухание",              0.5,   0.98),
    ("jitter",        "Дрожание",               0.0,   0.05),
    ("dt",            "Скорость симуляции",     0.1,   1.5),
]

GEN_HEIGHT = 2.6   # вертикальный шаг между "домашними" линиями поколений

DRAG_CATCH_RADIUS = 0.34
FRAME_INTERVAL_MS = 16   # ~60 fps

# анимация поэтапного появления при пересборке (как в Obsidian: узлы
# всплывают по одному, затем прорисовываются связи)
REVEAL_FRAMES_PER_NODE = 3
REVEAL_FRAMES_PER_EDGE = 1

# ---------- геометрия выезжающей панели настроек ----------
PANEL_WIDTH       = 0.24
PANEL_BOTTOM      = 0.08
PANEL_HEIGHT_FRAC = 0.86
PANEL_OPEN_X      = 0.73
PANEL_CLOSED_X    = 1.03
PANEL_EASE        = 0.25


def show():
    plt.rcParams["toolbar"] = "None"

    G = nx.DiGraph()
    for f in freddies:
        G.add_node(f)
    for child in freddies:
        for parent in child.parents:
            G.add_edge(parent, child)

    if not G.nodes:
        print("Генеалогическое дерево пустое.")
        return

    params = dict(DEFAULT_PARAMS)

    # ---------- Индексация узлов и связей под numpy ----------
    nodes = list(G.nodes)
    edges = list(G.edges)
    n = len(nodes)
    node_index = {node: i for i, node in enumerate(nodes)}
    parent_idx = np.array([node_index[p] for p, _ in edges], dtype=int)
    child_idx = np.array([node_index[c] for _, c in edges], dtype=int)

    generations = {}
    for node in nodes:
        generations.setdefault(node.generation, []).append(node)
    gens_present = sorted(generations.keys())

    def gen_y(gen):
        return -gen * GEN_HEIGHT

    gen_target_y = np.array([gen_y(node.generation) for node in nodes])

    # ---------- Начальные позиции (numpy) ----------
    pos = np.zeros((n, 2))
    vel = np.zeros((n, 2))
    dragged_mask = np.zeros(n, dtype=bool)

    def layout_by_generation(spring_len, spread_x, spread_y):
        for gen, gnodes in generations.items():
            width = max(len(gnodes), 1)
            for i, node in enumerate(gnodes):
                idx = node_index[node]
                pos[idx, 0] = (i - (width - 1) / 2) * spring_len * 1.3 + random.uniform(-spread_x, spread_x)
                pos[idx, 1] = gen_y(gen) + random.uniform(-spread_y, spread_y)
                vel[idx] = 0.0

    layout_by_generation(DEFAULT_PARAMS["spring_len"], 0.4, 0.3)

    max_width = max((len(v) for v in generations.values()), default=1)
    x_limit = max(max_width * DEFAULT_PARAMS["spring_len"], 3.5) + 3.0
    y_top = gen_y(gens_present[0]) + 2.5
    y_bottom = gen_y(gens_present[-1]) - 2.5

    # ---------- Фигура ----------
    fig, ax = plt.subplots(figsize=(13, 8.5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    try:
        fig.canvas.manager.set_window_title("Генеалогическое древо")
    except Exception:
        pass
    plt.subplots_adjust(bottom=0.1, left=0.03, right=0.97, top=0.94)

    dragged_idx = {"i": None}

    # ---------------------------------------------------------
    #  ПОЭТАПНОЕ ПОЯВЛЕНИЕ (узлы, потом связи)
    # ---------------------------------------------------------
    reveal = {
        "active": False,
        "frame": 0,
        "node_order": list(range(n)),
        "node_i": n,
        "edge_order": list(range(len(edges))),
        "edge_i": len(edges),
    }

    def start_reveal():
        order = list(range(n))
        random.shuffle(order)
        eorder = list(range(len(edges)))
        random.shuffle(eorder)
        reveal.update(active=True, frame=0, node_order=order, node_i=0, edge_order=eorder, edge_i=0)

    def advance_reveal():
        if not reveal["active"]:
            return
        reveal["frame"] += 1
        if reveal["node_i"] < n:
            if reveal["frame"] % REVEAL_FRAMES_PER_NODE == 0:
                reveal["node_i"] += 1
        elif reveal["edge_i"] < len(edges):
            if reveal["frame"] % REVEAL_FRAMES_PER_EDGE == 0:
                reveal["edge_i"] += 1
        else:
            reveal["active"] = False

    # ---------------------------------------------------------
    #  ФИЗИКА (векторизовано на numpy — быстрее и компактнее)
    # ---------------------------------------------------------
    def compute_forces():
        diff = pos[:, None, :] - pos[None, :, :]           # (n, n, 2)
        dist_sq = np.sum(diff * diff, axis=-1)
        np.fill_diagonal(dist_sq, np.inf)
        dist = np.sqrt(dist_sq)
        dist_safe = np.where(dist < 1e-3, 1e-3, dist)

        repel = params["repulsion"] / np.where(dist_sq < 1e-6, 1e-6, dist_sq)
        forces = np.stack([
            np.sum(diff[..., 0] / dist_safe * repel, axis=1),
            np.sum(diff[..., 1] / dist_safe * repel, axis=1),
        ], axis=-1)

        if len(edges):
            pdiff = pos[child_idx] - pos[parent_idx]
            edist = np.sqrt(np.sum(pdiff * pdiff, axis=1))
            edist_safe = np.where(edist < 1e-3, 1e-3, edist)
            stretch = edist_safe - params["spring_len"]
            fmag = params["spring_k"] * stretch
            efx = pdiff[:, 0] / edist_safe * fmag
            efy = pdiff[:, 1] / edist_safe * fmag
            np.add.at(forces[:, 0], parent_idx, efx)
            np.add.at(forces[:, 1], parent_idx, efy)
            np.add.at(forces[:, 0], child_idx, -efx)
            np.add.at(forces[:, 1], child_idx, -efy)

        forces[:, 1] += (gen_target_y - pos[:, 1]) * params["gen_pull"]
        forces[:, 0] += -pos[:, 0] * params["center_pull"]
        forces += np.random.uniform(-params["jitter"], params["jitter"], size=(n, 2))
        return forces

    def step_physics():
        forces = compute_forces()
        free = ~dragged_mask
        dt = params["dt"]
        vel[free] = (vel[free] + forces[free] * dt) * params["damping"]
        pos[free] += vel[free] * dt

    # ---------------------------------------------------------
    #  ОТРИСОВКА
    # ---------------------------------------------------------
    def color_of(node):
        r, g, b = node.color[:3]
        return tuple(max(0, min(255, c)) / 255 for c in (r, g, b))

    def draw_graph():
        ax.clear()
        ax.set_facecolor(BG_COLOR)

        visible_nodes = set(reveal["node_order"][:reveal["node_i"]])
        visible_edges = set(reveal["edge_order"][:reveal["edge_i"]])

        for e_i in visible_edges:
            p_i, c_i = parent_idx[e_i], child_idx[e_i]
            x1, y1 = pos[p_i]
            x2, y2 = pos[c_i]
            ax.add_patch(FancyArrowPatch(
                (x1, y1), (x2, y2),
                connectionstyle="arc3,rad=0.0",
                arrowstyle="-|>",
                mutation_scale=13,
                color=EDGE_COLOR,
                linewidth=1.6,
                alpha=0.8,
                zorder=1,
                shrinkA=16, shrinkB=16,
            ))

        for i in visible_nodes:
            node = nodes[i]
            x, y = pos[i]
            color = color_of(node)
            is_dragged = dragged_idx["i"] == i

            for radius, alpha in ((0.34, 0.10), (0.27, 0.16), (0.21, 0.22)):
                ax.add_patch(Circle((x, y), radius, color=color, alpha=alpha, zorder=2, linewidth=0))

            ax.add_patch(Circle(
                (x, y), NODE_RADIUS, facecolor=color, zorder=3,
                edgecolor=(ACCENT_COLOR if is_dragged else "#ffffff"),
                linewidth=2.2 if is_dragged else 1.1,
            ))

            ax.text(x, y + 0.30, node.name, color=TEXT_COLOR, fontsize=9,
                    fontweight="bold", ha="center", va="bottom", zorder=4)
            ax.text(x, y - 0.30, f"Поколение {node.generation}", color=GEN_TEXT_COLOR,
                    fontsize=7, ha="center", va="top", zorder=4)

        ax.set_title("Генеалогическое древо", color=TEXT_COLOR, fontsize=14, pad=14)
        ax.set_xlim(-x_limit, x_limit)
        ax.set_ylim(y_bottom, y_top)
        # фиксируем пропорции 1:1, чтобы кружки оставались круглыми
        # при любом изменении размеров окна
        ax.set_aspect("equal", adjustable="box")
        ax.set_axis_off()

    # ---------------------------------------------------------
    #  ПЕРЕТАСКИВАНИЕ МЫШЬЮ
    # ---------------------------------------------------------
    def find_node(x, y):
        if x is None or y is None:
            return None
        dist = np.hypot(pos[:, 0] - x, pos[:, 1] - y)
        i = int(np.argmin(dist))
        return i if dist[i] < DRAG_CATCH_RADIUS else None

    def on_press(event):
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            return
        i = find_node(event.xdata, event.ydata)
        dragged_idx["i"] = i
        if i is not None:
            dragged_mask[i] = True
            vel[i] = 0.0

    def on_motion(event):
        i = dragged_idx["i"]
        if i is None or event.inaxes != ax or event.xdata is None or event.ydata is None:
            return
        pos[i] = (event.xdata, event.ydata)

    def on_release(event):
        i = dragged_idx["i"]
        if i is not None:
            dragged_mask[i] = False
        dragged_idx["i"] = None

    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("motion_notify_event", on_motion)
    fig.canvas.mpl_connect("button_release_event", on_release)

    # ---------------------------------------------------------
    #  КНОПКА "ПЕРЕСОБРАТЬ" — новая раскладка + каскадное появление
    # ---------------------------------------------------------
    def regenerate(event):
        layout_by_generation(params["spring_len"], 0.5, 0.4)
        vel[:] = np.random.uniform(-0.6, 0.6, size=(n, 2))
        start_reveal()

    button_ax = fig.add_axes([0.77, 0.015, 0.2, 0.055])
    button_ax.set_facecolor(PANEL_COLOR)
    regenerate_button = Button(button_ax, "⟳ Пересобрать", color=PANEL_COLOR, hovercolor=PANEL_HOVER)
    regenerate_button.label.set_color(TEXT_COLOR)
    regenerate_button.label.set_fontsize(10)
    regenerate_button.on_clicked(regenerate)

    # ---------------------------------------------------------
    #  ВЫЕЗЖАЮЩАЯ ПАНЕЛЬ НАСТРОЕК (как шестерёнка в Obsidian).
    #  По умолчанию панель закрыта (спрятана за правым краем окна).
    # ---------------------------------------------------------
    panel_state = {"x": PANEL_CLOSED_X, "target_x": PANEL_CLOSED_X, "open": False}

    panel_bg_ax = fig.add_axes([PANEL_CLOSED_X, PANEL_BOTTOM, PANEL_WIDTH, PANEL_HEIGHT_FRAC])
    panel_bg_ax.set_facecolor(PANEL_COLOR)
    panel_bg_ax.set_xticks([])
    panel_bg_ax.set_yticks([])
    for spine in panel_bg_ax.spines.values():
        spine.set_visible(False)
    panel_bg_ax.set_zorder(10)

    title_open_x = PANEL_OPEN_X + 0.02
    title_y = PANEL_BOTTOM + PANEL_HEIGHT_FRAC - 0.045
    title_text = fig.text(title_open_x, title_y, "Параметры симуляции",
                           color=TEXT_COLOR, fontsize=11, fontweight="bold", zorder=11)

    slider_axes_info = []   # (ax, open_x, y, w, h)
    label_texts_info = []   # (text_obj, open_x, y)
    sliders = []

    row_top = PANEL_BOTTOM + PANEL_HEIGHT_FRAC - 0.11
    row_gap = 0.075
    row_h = 0.026

    def update_param(key, val):
        params[key] = val

    for idx, (key, label, vmin, vmax) in enumerate(SLIDERS):
        y = row_top - idx * row_gap
        open_x = PANEL_OPEN_X + 0.035
        w = PANEL_WIDTH - 0.07
        label_open_x = PANEL_OPEN_X + 0.03
        label_y = y + row_h + 0.018

        txt = fig.text(label_open_x, label_y, label, color=TEXT_COLOR, fontsize=8.5, zorder=11)
        label_texts_info.append((txt, label_open_x, label_y))

        slider_ax = fig.add_axes([open_x, y, w, row_h])
        slider_ax.set_zorder(11)
        slider_ax.set_facecolor(PANEL_HOVER)
        slider = Slider(slider_ax, "", vmin, vmax, valinit=params[key], color=ACCENT_COLOR)
        slider.valtext.set_color(TEXT_COLOR)
        slider.valtext.set_fontsize(7.5)
        slider.on_changed(partial(update_param, key))

        slider_axes_info.append((slider_ax, open_x, y, w, row_h))
        sliders.append(slider)

    reset_y = row_top - len(SLIDERS) * row_gap - 0.01
    reset_open_x = PANEL_OPEN_X + 0.035
    reset_w = PANEL_WIDTH - 0.07
    reset_h = 0.045
    reset_button_ax = fig.add_axes([reset_open_x, reset_y, reset_w, reset_h])
    reset_button_ax.set_zorder(11)
    reset_button = Button(reset_button_ax, "Сбросить настройки", color=PANEL_HOVER, hovercolor=ACCENT_COLOR)
    reset_button.label.set_color(TEXT_COLOR)
    reset_button.label.set_fontsize(8.5)
    reset_button.on_clicked(lambda event: [s.reset() for s in sliders])

    def sync_panel_positions():
        delta = panel_state["x"] - PANEL_OPEN_X
        panel_bg_ax.set_position([PANEL_OPEN_X + delta, PANEL_BOTTOM, PANEL_WIDTH, PANEL_HEIGHT_FRAC])
        title_text.set_position((title_open_x + delta, title_y))
        for ax_s, open_x, y, w, h in slider_axes_info:
            ax_s.set_position([open_x + delta, y, w, h])
        for txt, open_x, y in label_texts_info:
            txt.set_position((open_x + delta, y))
        reset_button_ax.set_position([reset_open_x + delta, reset_y, reset_w, reset_h])

    # приводим панель и все её элементы в закрытое состояние сразу,
    # до первого кадра — иначе слайдеры на миг "висят в воздухе"
    sync_panel_positions()

    def toggle_panel(event):
        panel_state["open"] = not panel_state["open"]
        panel_state["target_x"] = PANEL_OPEN_X if panel_state["open"] else PANEL_CLOSED_X

    gear_button_ax = fig.add_axes([0.955, 0.925, 0.038, 0.05])
    gear_button = Button(gear_button_ax, "⚙", color=PANEL_COLOR, hovercolor=PANEL_HOVER)
    gear_button.label.set_color(TEXT_COLOR)
    gear_button.label.set_fontsize(13)
    gear_button.on_clicked(toggle_panel)

    # ---------------------------------------------------------
    #  ЦИКЛ АНИМАЦИИ
    # ---------------------------------------------------------
    def animate(frame):
        step_physics()
        advance_reveal()
        draw_graph()

        if panel_state["x"] != panel_state["target_x"]:
            panel_state["x"] += (panel_state["target_x"] - panel_state["x"]) * PANEL_EASE
            if abs(panel_state["target_x"] - panel_state["x"]) < 0.0015:
                panel_state["x"] = panel_state["target_x"]
            sync_panel_positions()

        return []

    draw_graph()
    anim = FuncAnimation(fig, animate, interval=FRAME_INTERVAL_MS, cache_frame_data=False)
    fig._tree_animation_ref = anim

    plt.show()
