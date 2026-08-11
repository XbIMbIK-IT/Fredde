import math
import random

import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.patches import Circle, FancyArrowPatch
from matplotlib.animation import FuncAnimation

from fredde import freddis


# ============================================================
#  ВИЗУАЛЬНЫЕ НАСТРОЙКИ (тёмная тема в стиле Obsidian)
# ============================================================
BG_COLOR        = "#202225"   # фон окна и осей
PANEL_COLOR     = "#2b2d31"   # фон панели с кнопкой
PANEL_HOVER     = "#3b3d42"
EDGE_COLOR      = "#5a5d63"   # цвет связей родитель -> ребёнок
TEXT_COLOR      = "#dcddde"   # цвет подписей узлов
GEN_LINE_COLOR  = "#33353a"   # цвет линий-разделителей поколений
GEN_TEXT_COLOR  = "#75787f"   # цвет подписи "Поколение N"
ACCENT_COLOR    = "#7289da"   # обводка узла, который сейчас тащат мышью

# ============================================================
#  ФИЗИКА (аналог "force graph" в Obsidian)
# ============================================================
REPULSION       = 0.9     # сила взаимного отталкивания узлов друг от друга
SPRING_LEN      = 1.7     # желаемая длина связи родитель -> ребёнок
SPRING_K        = 0.03    # жёсткость этой "пружины"
GEN_PULL        = 0.06    # притяжение узла к своей линии поколения по Y
CENTER_PULL     = 0.004   # лёгкое притяжение к центру, чтобы дерево не расползалось
DAMPING         = 0.86    # затухание скорости (имитация вязкости)
JITTER          = 0.010   # амплитуда случайного "покачивания" на каждом кадре
DT              = 0.7     # шаг интегрирования
GEN_HEIGHT      = 2.6     # вертикальное расстояние между поколениями

DRAG_CATCH_RADIUS  = 0.34  # насколько близко нужно кликнуть, чтобы "схватить" узел
FRAME_INTERVAL_MS  = 33    # ~30 fps


def show():
    # прячем верхнюю панель matplotlib (лупы, стрелки, настройки осей и т.д.)
    plt.rcParams["toolbar"] = "None"

    G = nx.DiGraph()
    for f in freddis:
        G.add_node(f)
    for child in freddis:
        for parent in child.parents:
            G.add_edge(parent, child)

    if not G.nodes:
        print("Генеалогическое дерево пустое.")
        return

    # ---------- Группируем узлы по поколениям ----------
    generations = {}
    for node in G.nodes:
        generations.setdefault(node.generation, []).append(node)
    gens_present = sorted(generations.keys())

    def gen_y(gen):
        # поколение 0 сверху, дальше дерево растёт вниз
        return -gen * GEN_HEIGHT

    # ---------- Начальные позиции: по поколениям, X — случайно ----------
    pos = {}
    vel = {node: [0.0, 0.0] for node in G.nodes}

    for gen, nodes in generations.items():
        width = max(len(nodes), 1)
        for i, node in enumerate(nodes):
            x = (i - (width - 1) / 2) * SPRING_LEN * 1.3 + random.uniform(-0.3, 0.3)
            y = gen_y(gen) + random.uniform(-0.15, 0.15)
            pos[node] = [x, y]

    # ---------- Границы обзора считаем один раз, чтобы камера не "тряслась" вместе с узлами ----------
    max_width = max((len(v) for v in generations.values()), default=1)
    x_limit = max(max_width * SPRING_LEN * 0.9, 3.0) + 2.5
    y_top = gen_y(gens_present[0]) + 1.8
    y_bottom = gen_y(gens_present[-1]) - 1.8

    # ---------- Фигура ----------
    fig, ax = plt.subplots(figsize=(13, 8.5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    try:
        fig.canvas.manager.set_window_title("Генеалогическое древо")
    except Exception:
        pass
    plt.subplots_adjust(bottom=0.1, left=0.03, right=0.97, top=0.94)

    dragged_node = {"node": None}
    paused_nodes = set()   # узлы, которые сейчас не участвуют в физике (их тащит мышь)

    # ---------------------------------------------------------
    #  ФИЗИЧЕСКАЯ СИМУЛЯЦИЯ
    # ---------------------------------------------------------
    def compute_forces():
        forces = {node: [0.0, 0.0] for node in G.nodes}
        nodes_list = list(G.nodes)

        # взаимное отталкивание всех узлов друг от друга (кулоновское)
        for i in range(len(nodes_list)):
            a = nodes_list[i]
            ax_, ay_ = pos[a]
            for j in range(i + 1, len(nodes_list)):
                b = nodes_list[j]
                dx = ax_ - pos[b][0]
                dy = ay_ - pos[b][1]
                dist_sq = dx * dx + dy * dy
                dist = math.sqrt(dist_sq) or 0.001
                f = REPULSION / dist_sq
                fx, fy = dx / dist * f, dy / dist * f
                forces[a][0] += fx
                forces[a][1] += fy
                forces[b][0] -= fx
                forces[b][1] -= fy

        # притяжение вдоль родственных связей ("пружины")
        for parent, child in G.edges:
            dx = pos[child][0] - pos[parent][0]
            dy = pos[child][1] - pos[parent][1]
            dist = math.sqrt(dx * dx + dy * dy) or 0.001
            stretch = dist - SPRING_LEN
            f = SPRING_K * stretch
            fx, fy = dx / dist * f, dy / dist * f
            forces[parent][0] += fx
            forces[parent][1] += fy
            forces[child][0] -= fx
            forces[child][1] -= fy

        # притяжение к своей линии поколения + к центру + случайное покачивание
        for node in G.nodes:
            target_y = gen_y(node.generation)
            forces[node][1] += (target_y - pos[node][1]) * GEN_PULL
            forces[node][0] += -pos[node][0] * CENTER_PULL
            forces[node][0] += random.uniform(-JITTER, JITTER)
            forces[node][1] += random.uniform(-JITTER, JITTER)

        return forces

    def step_physics():
        forces = compute_forces()
        for node in G.nodes:
            if node in paused_nodes:
                continue
            vx, vy = vel[node]
            fx, fy = forces[node]
            vx = (vx + fx * DT) * DAMPING
            vy = (vy + fy * DT) * DAMPING
            vel[node] = [vx, vy]
            pos[node][0] += vx * DT
            pos[node][1] += vy * DT

    # ---------------------------------------------------------
    #  ОТРИСОВКА
    # ---------------------------------------------------------
    def color_of(node):
        r, g, b = node.color[:3]
        return tuple(max(0, min(255, c)) / 255 for c in (r, g, b))

    def draw_graph():
        ax.clear()
        ax.set_facecolor(BG_COLOR)

        # линии-разделители поколений
        for gen in gens_present:
            y = gen_y(gen)
            ax.axhline(y, color=GEN_LINE_COLOR, linewidth=1, linestyle="--", zorder=0)
            ax.text(
                -x_limit + 0.25, y + 0.12, f"Поколение {gen}",
                color=GEN_TEXT_COLOR, fontsize=9, fontweight="bold",
                ha="left", va="bottom", zorder=0,
            )

        # рёбра родитель -> ребёнок, лёгкой дугой
        for parent, child in G.edges:
            x1, y1 = pos[parent]
            x2, y2 = pos[child]
            arrow = FancyArrowPatch(
                (x1, y1), (x2, y2),
                connectionstyle="arc3,rad=0.12",
                arrowstyle="-|>",
                mutation_scale=13,
                color=EDGE_COLOR,
                linewidth=1.6,
                alpha=0.8,
                zorder=1,
                shrinkA=16, shrinkB=16,
            )
            ax.add_patch(arrow)

        # узлы с мягким "свечением"
        for node in G.nodes:
            x, y = pos[node]
            color = color_of(node)
            is_dragged = node is dragged_node["node"]

            for radius, alpha in ((0.34, 0.10), (0.27, 0.16), (0.21, 0.22)):
                ax.add_patch(Circle((x, y), radius, color=color, alpha=alpha, zorder=2, linewidth=0))

            ax.add_patch(Circle(
                (x, y), 0.16, facecolor=color, zorder=3,
                edgecolor=(ACCENT_COLOR if is_dragged else "#ffffff"),
                linewidth=2.2 if is_dragged else 1.1,
            ))

            ax.text(
                x, y - 0.28, node.name,
                color=TEXT_COLOR, fontsize=9, fontweight="bold",
                ha="center", va="top", zorder=4,
            )

        ax.set_title("Генеалогическое древо", color=TEXT_COLOR, fontsize=14, pad=14)
        ax.set_xlim(-x_limit, x_limit)
        ax.set_ylim(y_bottom, y_top)
        ax.set_axis_off()

    # ---------------------------------------------------------
    #  ПЕРЕТАСКИВАНИЕ МЫШЬЮ
    # ---------------------------------------------------------
    def find_node(x, y):
        if x is None or y is None:
            return None
        closest_node = None
        closest_distance = float("inf")
        for node, (nx_pos, ny_pos) in pos.items():
            distance = math.hypot(nx_pos - x, ny_pos - y)
            if distance < DRAG_CATCH_RADIUS and distance < closest_distance:
                closest_distance = distance
                closest_node = node
        return closest_node

    def on_press(event):
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            return
        node = find_node(event.xdata, event.ydata)
        dragged_node["node"] = node
        if node is not None:
            paused_nodes.add(node)
            vel[node] = [0.0, 0.0]

    def on_motion(event):
        node = dragged_node["node"]
        if node is None or event.inaxes != ax:
            return
        if event.xdata is None or event.ydata is None:
            return
        pos[node][0] = event.xdata
        pos[node][1] = event.ydata

    def on_release(event):
        node = dragged_node["node"]
        if node is not None:
            paused_nodes.discard(node)
        dragged_node["node"] = None

    # ---------------------------------------------------------
    #  КНОПКА "ПЕРЕСОБРАТЬ"
    # ---------------------------------------------------------
    def regenerate(event):
        for gen, nodes in generations.items():
            width = max(len(nodes), 1)
            for i, node in enumerate(nodes):
                pos[node][0] = (i - (width - 1) / 2) * SPRING_LEN * 1.3 + random.uniform(-0.5, 0.5)
                pos[node][1] = gen_y(gen) + random.uniform(-0.4, 0.4)
                vel[node] = [random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.6)]

    button_ax = fig.add_axes([0.77, 0.015, 0.2, 0.055])
    button_ax.set_facecolor(PANEL_COLOR)
    regenerate_button = Button(
        button_ax, "⟳ Пересобрать",
        color=PANEL_COLOR, hovercolor=PANEL_HOVER,
    )
    regenerate_button.label.set_color(TEXT_COLOR)
    regenerate_button.label.set_fontsize(10)
    regenerate_button.on_clicked(regenerate)

    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("motion_notify_event", on_motion)
    fig.canvas.mpl_connect("button_release_event", on_release)

    # ---------------------------------------------------------
    #  ЦИКЛ АНИМАЦИИ
    # ---------------------------------------------------------
    def animate(frame):
        step_physics()
        draw_graph()
        return []

    draw_graph()
    anim = FuncAnimation(fig, animate, interval=FRAME_INTERVAL_MS, cache_frame_data=False)
    fig._tree_animation_ref = anim  # чтобы объект не был уничтожен сборщиком мусора

    plt.show()
