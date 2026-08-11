import math
import random

import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider
from matplotlib.patches import Circle, FancyArrowPatch
from matplotlib.animation import FuncAnimation

from fredde import freddis


# ============================================================
#  ВИЗУАЛЬНЫЕ НАСТРОЙКИ (тёмная тема в стиле Obsidian)
# ============================================================
BG_COLOR        = "#202225"   # фон окна и осей
PANEL_COLOR     = "#2b2d31"   # фон панели настроек / кнопок
PANEL_HOVER     = "#3b3d42"
EDGE_COLOR      = "#5a5d63"   # цвет связей родитель -> ребёнок
TEXT_COLOR      = "#dcddde"   # цвет имени узла
GEN_TEXT_COLOR  = "#75787f"   # цвет подписи поколения под узлом
ACCENT_COLOR    = "#7289da"   # обводка узла при перетаскивании / акцент слайдеров

# ============================================================
#  ФИЗИКА (аналог "force graph" в Obsidian) — теперь регулируется
#  ползунками во время работы, значения ниже — только стартовые.
#  gen_pull специально сделан слабым: поколения задают лишь лёгкий
#  вертикальный дрейф, а не жёсткие ряды, чтобы граф не превращался
#  в застывшее дерево, а вёл себя как органичное "облако" узлов.
# ============================================================
DEFAULT_PARAMS = {
    "repulsion":   1.15,   # взаимное отталкивание узлов
    "spring_len":  1.9,    # желаемая длина связи родитель -> ребёнок
    "spring_k":    0.03,   # жёсткость этой "пружины"
    "gen_pull":    0.015,  # слабое притяжение к своему поколению по Y
    "center_pull": 0.004,  # лёгкое притяжение к центру
    "damping":     0.86,   # затухание скорости (вязкость)
    "jitter":      0.010,  # амплитуда случайного покачивания за кадр
    "dt":          0.7,    # шаг интегрирования
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

GEN_HEIGHT = 2.6   # вертикальное расстояние между "домашними" линиями поколений

DRAG_CATCH_RADIUS  = 0.34   # насколько близко нужно кликнуть, чтобы "схватить" узел
FRAME_INTERVAL_MS  = 33     # ~30 fps

# ---------- геометрия выезжающей панели настроек ----------
PANEL_WIDTH       = 0.24
PANEL_BOTTOM      = 0.08
PANEL_HEIGHT_FRAC = 0.86
PANEL_OPEN_X      = 0.73   # левый край панели, когда она выехала
PANEL_CLOSED_X    = 1.03   # левый край панели, когда она спрятана за краем окна
PANEL_EASE        = 0.25   # скорость анимации выезда/заезда (0..1 за кадр)


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

    params = dict(DEFAULT_PARAMS)

    # ---------- Группируем узлы по поколениям (только для стартовой раскладки) ----------
    generations = {}
    for node in G.nodes:
        generations.setdefault(node.generation, []).append(node)
    gens_present = sorted(generations.keys())

    def gen_y(gen):
        # поколение 0 сверху, дальше дерево растёт вниз
        return -gen * GEN_HEIGHT

    # ---------- Начальные позиции: по поколениям, X — случайно ----------
    # Это только отправная точка. Дальше физика с малым gen_pull быстро
    # "расслабляет" раскладку в органичное облако, а не держит жёсткие ряды.
    pos = {}
    vel = {node: [0.0, 0.0] for node in G.nodes}

    for gen, nodes in generations.items():
        width = max(len(nodes), 1)
        for i, node in enumerate(nodes):
            x = (i - (width - 1) / 2) * DEFAULT_PARAMS["spring_len"] * 1.3 + random.uniform(-0.4, 0.4)
            y = gen_y(gen) + random.uniform(-0.3, 0.3)
            pos[node] = [x, y]

    # ---------- Границы обзора считаем один раз, чтобы камера не "тряслась" вместе с узлами ----------
    max_width = max((len(v) for v in generations.values()), default=1)
    x_limit = max(max_width * DEFAULT_PARAMS["spring_len"] * 1.0, 3.5) + 3.0
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

    dragged_node = {"node": None}
    paused_nodes = set()   # узлы, которые сейчас не участвуют в физике (их тащит мышь)

    # ---------------------------------------------------------
    #  ФИЗИЧЕСКАЯ СИМУЛЯЦИЯ
    # ---------------------------------------------------------
    def compute_forces():
        forces = {node: [0.0, 0.0] for node in G.nodes}
        nodes_list = list(G.nodes)

        repulsion = params["repulsion"]
        spring_len = params["spring_len"]
        spring_k = params["spring_k"]
        gen_pull = params["gen_pull"]
        center_pull = params["center_pull"]
        jitter = params["jitter"]

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
                f = repulsion / dist_sq
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
            stretch = dist - spring_len
            f = spring_k * stretch
            fx, fy = dx / dist * f, dy / dist * f
            forces[parent][0] += fx
            forces[parent][1] += fy
            forces[child][0] -= fx
            forces[child][1] -= fy

        # слабое притяжение к своей линии поколения + к центру + покачивание
        for node in G.nodes:
            target_y = gen_y(node.generation)
            forces[node][1] += (target_y - pos[node][1]) * gen_pull
            forces[node][0] += -pos[node][0] * center_pull
            forces[node][0] += random.uniform(-jitter, jitter)
            forces[node][1] += random.uniform(-jitter, jitter)

        return forces

    def step_physics():
        forces = compute_forces()
        damping = params["damping"]
        dt = params["dt"]
        for node in G.nodes:
            if node in paused_nodes:
                continue
            vx, vy = vel[node]
            fx, fy = forces[node]
            vx = (vx + fx * dt) * damping
            vy = (vy + fy * dt) * damping
            vel[node] = [vx, vy]
            pos[node][0] += vx * dt
            pos[node][1] += vy * dt

    # ---------------------------------------------------------
    #  ОТРИСОВКА
    # ---------------------------------------------------------
    def color_of(node):
        r, g, b = node.color[:3]
        return tuple(max(0, min(255, c)) / 255 for c in (r, g, b))

    def draw_graph():
        ax.clear()
        ax.set_facecolor(BG_COLOR)

        # рёбра родитель -> ребёнок — прямые линии, без дуги
        for parent, child in G.edges:
            x1, y1 = pos[parent]
            x2, y2 = pos[child]
            arrow = FancyArrowPatch(
                (x1, y1), (x2, y2),
                connectionstyle="arc3,rad=0.0",
                arrowstyle="-|>",
                mutation_scale=13,
                color=EDGE_COLOR,
                linewidth=1.6,
                alpha=0.8,
                zorder=1,
                shrinkA=16, shrinkB=16,
            )
            ax.add_patch(arrow)

        # узлы с мягким "свечением"; поколение теперь подписано прямо
        # под самим узлом, а не привязано к общей фоновой линии
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

            # имя — над узлом
            ax.text(
                x, y + 0.30, node.name,
                color=TEXT_COLOR, fontsize=9, fontweight="bold",
                ha="center", va="bottom", zorder=4,
            )
            # поколение — под узлом
            ax.text(
                x, y - 0.30, f"Поколение {node.generation}",
                color=GEN_TEXT_COLOR, fontsize=7,
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
                pos[node][0] = (i - (width - 1) / 2) * params["spring_len"] * 1.3 + random.uniform(-0.5, 0.5)
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

    # ---------------------------------------------------------
    #  ВЫЕЗЖАЮЩАЯ ПАНЕЛЬ НАСТРОЕК СИМУЛЯЦИИ (как шестерёнка в Obsidian)
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
    title_text = fig.text(
        PANEL_CLOSED_X + 0.02, title_y,
        "Параметры симуляции",
        color=TEXT_COLOR, fontsize=11, fontweight="bold", zorder=11,
    )

    slider_axes_info = []   # (ax, open_x, y, w, h)
    label_texts_info = []   # (text_obj, open_x, y)
    sliders = []

    row_top = PANEL_BOTTOM + PANEL_HEIGHT_FRAC - 0.11
    row_gap = 0.075
    row_h = 0.026

    for idx, (key, label, vmin, vmax) in enumerate(SLIDERS):
        y = row_top - idx * row_gap
        open_x = PANEL_OPEN_X + 0.035
        w = PANEL_WIDTH - 0.07

        label_open_x = PANEL_OPEN_X + 0.03
        label_y = y + row_h + 0.018
        txt = fig.text(
            label_open_x, label_y, label,
            color=TEXT_COLOR, fontsize=8.5, zorder=11,
        )
        label_texts_info.append((txt, label_open_x, label_y))

        slider_ax = fig.add_axes([open_x, y, w, row_h])
        slider_ax.set_zorder(11)
        slider_ax.set_facecolor(PANEL_HOVER)
        slider = Slider(
            slider_ax, "", vmin, vmax,
            valinit=params[key], color=ACCENT_COLOR,
        )
        slider.valtext.set_color(TEXT_COLOR)
        slider.valtext.set_fontsize(7.5)

        def make_callback(param_key):
            def _cb(val, k=param_key):
                params[k] = val
            return _cb

        slider.on_changed(make_callback(key))

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

    def reset_params(event):
        for slider in sliders:
            slider.reset()

    reset_button.on_clicked(reset_params)

    def sync_panel_positions():
        delta = panel_state["x"] - PANEL_OPEN_X
        panel_bg_ax.set_position([PANEL_OPEN_X + delta, PANEL_BOTTOM, PANEL_WIDTH, PANEL_HEIGHT_FRAC])
        title_text.set_position((title_open_x + delta, title_y))
        for ax_s, open_x, y, w, h in slider_axes_info:
            ax_s.set_position([open_x + delta, y, w, h])
        for txt, open_x, y in label_texts_info:
            txt.set_position((open_x + delta, y))
        reset_button_ax.set_position([reset_open_x + delta, reset_y, reset_w, reset_h])

    def toggle_panel(event):
        panel_state["open"] = not panel_state["open"]
        panel_state["target_x"] = PANEL_OPEN_X if panel_state["open"] else PANEL_CLOSED_X

    gear_button_ax = fig.add_axes([0.955, 0.925, 0.038, 0.05])
    gear_button = Button(gear_button_ax, "⚙", color=PANEL_COLOR, hovercolor=PANEL_HOVER)
    gear_button.label.set_color(TEXT_COLOR)
    gear_button.label.set_fontsize(13)
    gear_button.on_clicked(toggle_panel)

    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("motion_notify_event", on_motion)
    fig.canvas.mpl_connect("button_release_event", on_release)

    # ---------------------------------------------------------
    #  ЦИКЛ АНИМАЦИИ
    # ---------------------------------------------------------
    def animate(frame):
        step_physics()
        draw_graph()

        if panel_state["x"] != panel_state["target_x"]:
            panel_state["x"] += (panel_state["target_x"] - panel_state["x"]) * PANEL_EASE
            if abs(panel_state["target_x"] - panel_state["x"]) < 0.0015:
                panel_state["x"] = panel_state["target_x"]
            sync_panel_positions()

        return []

    draw_graph()
    anim = FuncAnimation(fig, animate, interval=FRAME_INTERVAL_MS, cache_frame_data=False)
    fig._tree_animation_ref = anim  # чтобы объект не был уничтожен сборщиком мусора

    plt.show()
