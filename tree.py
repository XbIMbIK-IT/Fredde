import random
from functools import partial

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider
from matplotlib.patches import Circle
from matplotlib.collections import LineCollection
from matplotlib.animation import FuncAnimation

try:
    from scipy.spatial import cKDTree
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False

from fredde import freddies

from freddePhoto import generate_fredde


# ============================================================
#  ВИЗУАЛЬНЫЕ НАСТРОЙКИ (тёмная тема в стиле Obsidian)
# ============================================================
BG_COLOR       = "#202225"   # фон окна и осей
PANEL_COLOR    = "#2b2d31"   # фон панели настроек / кнопок
PANEL_HOVER    = "#3b3d42"
EDGE_COLOR     = "#5a5d63"   # цвет связей родитель -> ребёнок
ARROW_COLOR    = "#9aa0a8"   # цвет наконечника стрелки (ярче линии)
TEXT_COLOR     = "#dcddde"   # цвет имени узла
GEN_TEXT_COLOR = "#75787f"   # цвет подписи поколения под узлом
ACCENT_COLOR   = "#7289da"   # обводка узла при перетаскивании / акцент слайдеров

# Размер картинки фредика теперь задаётся в координатах данных (а не в
# экранных пикселях), поэтому при зуме колёсиком картинки будут
# уменьшаться/увеличиваться вместе со всей сценой, как и положено.
NODE_IMG_HALF   = 0.50        # "радиус" картинки фредика в данных
HIT_RADIUS      = NODE_IMG_HALF * 1.45   # хитбокс клика/наведения - с запасом, удобнее попадать
EDGE_SHRINK     = NODE_IMG_HALF * 0.95   # не даём линии связи заходить под картинку
ARROW_LEN       = 0.16
ARROW_WIDTH_DEG = 22

# ============================================================
#  ФИЗИКА (аналог "force graph" в Obsidian), регулируется ползунками.
# ============================================================
DEFAULT_PARAMS = {
    "repulsion":   1,
    "spring_len":  1.5,
    "spring_k":    0.03,
    "center_pull": 0.02,
    "damping":     0.86,
    "jitter":      0.010,
    "dt":          0.7,
}

SLIDERS = [
    ("repulsion",     "Отталкивание узлов",     0.1,   3.0),
    ("spring_len",    "Длина связи",            0.5,   4.0),
    ("spring_k",      "Жёсткость связи",        0.0,   0.12),
    ("center_pull",   "Тяга к центру",          0.0,   0.02),
    ("damping",       "Затухание",              0.5,   0.98),
    ("jitter",        "Дрожание",               0.0,   0.05),
    ("dt",            "Скорость симуляции",     0.1,   1.5),
]

GEN_HEIGHT = 2.6

FRAME_INTERVAL_MS = 16   # ~60 fps, пока симуляция "бодрствует"

REVEAL_FRAMES_PER_NODE = 3
REVEAL_FRAMES_PER_EDGE = 1

# ---------- усыпление симуляции, когда всё устаканилось ----------
SLEEP_MOVE_EPS = 0.0006
SLEEP_FRAMES_NEEDED = 90

# ---------- геометрия выезжающей панели настроек ----------
PANEL_WIDTH       = 0.24
PANEL_BOTTOM      = 0.08
PANEL_HEIGHT_FRAC = 0.86
PANEL_OPEN_X      = 0.73
PANEL_CLOSED_X    = 1.03
PANEL_EASE        = 0.25

# ---------- зум колёсиком мыши ----------
ZOOM_IN_FACTOR  = 0.9
ZOOM_OUT_FACTOR = 1.0 / 0.9
MIN_VIEW_SPAN   = 1.5    # ближе не подпустим, а то совсем ничего не видно
MAX_VIEW_ZOOM_OUT = 4.0  # во сколько раз можно отдалиться от начального вида

# ---------- отталкивание узлов ----------
# За этим расстоянием сила отталкивания пренебрежимо мала (репульсия падает
# как 1/r^2), поэтому дальние пары узлов в расчёте вообще не участвуют.
# Именно это и даёт основной прирост скорости: раньше на каждый кадр считалась
# полная матрица n x n для ВСЕХ пар узлов, даже тех, что были на разных концах
# экрана и почти не влияли друг на друга.
REPULSION_CUTOFF = 10.0

GENDER_LABELS = {
    "boy": "мальчик",
    "girl": "девочка",
    "is": "интерсекс",
    "cf": "чайлдфри",
}


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

    # ---------- Начальные позиции (numpy) ----------
    pos = np.zeros((n, 2))
    prev_pos = np.zeros((n, 2))
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
    prev_pos[:] = pos

    max_width = max((len(v) for v in generations.values()), default=1)
    x_limit = max(max_width * DEFAULT_PARAMS["spring_len"], 3.5) + 3.0
    y_top = gen_y(gens_present[0]) + 2.5
    y_bottom = gen_y(gens_present[-1]) - 2.5
    home_xlim = (-x_limit, x_limit)
    home_ylim = (y_bottom, y_top)

    # ---------- Фигура ----------
    fig, ax = plt.subplots(figsize=(13, 8.5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    try:
        fig.canvas.manager.set_window_title("Генеалогическое древо")
    except Exception:
        pass
    plt.subplots_adjust(bottom=0.1, left=0.03, right=0.97, top=0.94)

    ax.set_title("Генеалогическое древо", color=TEXT_COLOR, fontsize=14, pad=14)
    ax.set_xlim(*home_xlim)
    ax.set_ylim(*home_ylim)
    ax.set_aspect("equal", adjustable="box")
    ax.set_axis_off()

    dragged_idx = {"i": None}

    # ---------------------------------------------------------
    #  СПРАЙТЫ ФРЕДИКОВ (генерируются один раз, не каждый кадр!)
    # ---------------------------------------------------------
    def color_of(node):
        r, g, b = node.color[:3]
        return tuple(max(0, min(255, c)) / 255 for c in (r, g, b))

    sprite_arrays = [None] * n
    for i, node in enumerate(nodes):
        try:
            img = generate_fredde(node)
            sprite_arrays[i] = np.asarray(img)
        except Exception as e:
            print(f"Не удалось сгенерировать спрайт для {node.name}: {e}")
            sprite_arrays[i] = None

    # ---------------------------------------------------------
    #  ПОСТОЯННЫЕ ARTIST'Ы (создаются один раз, дальше только двигаются).
    #  Картинки рисуются через imshow с extent в координатах данных -
    #  тогда при зуме колёсиком они естественно масштабируются вместе
    #  со сценой, а не остаются "приклеенными" к экрану как AnnotationBbox.
    # ---------------------------------------------------------
    edge_collection = LineCollection([], colors=EDGE_COLOR, linewidths=2.4, alpha=0.85, zorder=1)
    ax.add_collection(edge_collection)

    arrow_collection = LineCollection([], colors=ARROW_COLOR, linewidths=2.2, alpha=0.95, zorder=1.5,
                                       capstyle="round", joinstyle="round")
    ax.add_collection(arrow_collection)

    halo_circles = []
    images = []
    fallback_dots = []
    name_texts = []
    gen_texts = []
    half_sizes = []   # половина ширины/высоты картинки в данных (с учётом пропорций спрайта)

    for i, node in enumerate(nodes):
        color = color_of(node)

        halo = Circle((0, 0), NODE_IMG_HALF * 1.35, color=color, alpha=0.15, zorder=2, linewidth=0)
        halo.set_visible(False)
        ax.add_patch(halo)
        halo_circles.append(halo)

        arr = sprite_arrays[i]
        if arr is not None:
            h, w = arr.shape[0], arr.shape[1]
            ratio = w / h if h else 1.0
            hw = NODE_IMG_HALF * (ratio if ratio >= 1 else 1.0)
            hh = NODE_IMG_HALF * (1.0 if ratio >= 1 else 1.0 / ratio)
            half_sizes.append((hw, hh))
            im = ax.imshow(arr, extent=(0, 0, 0, 0), zorder=3, interpolation="bilinear", origin="upper")
            im.set_visible(False)
            images.append(im)
            fallback_dots.append(None)
        else:
            half_sizes.append((NODE_IMG_HALF, NODE_IMG_HALF))
            images.append(None)
            dot = Circle((0, 0), NODE_IMG_HALF, facecolor=color, edgecolor="#ffffff",
                         linewidth=1.1, zorder=3)
            dot.set_visible(False)
            ax.add_patch(dot)
            fallback_dots.append(dot)

        nt = ax.text(0, 0, node.name, color=TEXT_COLOR, fontsize=9, fontweight="bold",
                     ha="center", va="bottom", zorder=4, visible=False)
        name_texts.append(nt)

        gt = ax.text(0, 0, f"Поколение {node.generation}", color=GEN_TEXT_COLOR,
                     fontsize=7, ha="center", va="top", zorder=4, visible=False)
        gen_texts.append(gt)

    tooltip = ax.annotate(
        "", xy=(0, 0), xytext=(18, 18), textcoords="offset points",
        va="bottom", ha="left", fontsize=13, color=TEXT_COLOR, zorder=20,
        linespacing=1.6,
        bbox=dict(boxstyle="round,pad=0.8", facecolor=PANEL_COLOR, edgecolor=ACCENT_COLOR,
                  alpha=0.97, linewidth=1.4),
    )
    tooltip.set_visible(False)
    hover_state = {"i": None}

    # ---------------------------------------------------------
    #  ПОЭТАПНОЕ ПОЯВЛЕНИЕ (узлы, потом связи)
    # ---------------------------------------------------------
    reveal = {
        "active": False,
        "frame": 0,
        "node_order": list(range(n)),
        "node_i": 0,
        "edge_order": list(range(len(edges))),
        "edge_i": 0,
    }
    revealed_edge_parent = np.array([], dtype=int)
    revealed_edge_child = np.array([], dtype=int)

    def hide_everything():
        for artist in halo_circles + name_texts + gen_texts:
            artist.set_visible(False)
        for im in images:
            if im is not None:
                im.set_visible(False)
        for dot in fallback_dots:
            if dot is not None:
                dot.set_visible(False)
        edge_collection.set_segments([])
        arrow_collection.set_segments([])

    def start_reveal():
        order = list(range(n))
        random.shuffle(order)
        eorder = list(range(len(edges)))
        random.shuffle(eorder)
        reveal.update(active=True, frame=0, node_order=order, node_i=0, edge_order=eorder, edge_i=0)
        hide_everything()

    def reveal_node(i):
        halo_circles[i].set_visible(True)
        name_texts[i].set_visible(True)
        gen_texts[i].set_visible(True)
        if images[i] is not None:
            images[i].set_visible(True)
        if fallback_dots[i] is not None:
            fallback_dots[i].set_visible(True)

    def advance_reveal():
        nonlocal revealed_edge_parent, revealed_edge_child
        if not reveal["active"]:
            return
        reveal["frame"] += 1

        if reveal["node_i"] < n:
            if reveal["frame"] % REVEAL_FRAMES_PER_NODE == 0:
                idx = reveal["node_order"][reveal["node_i"]]
                reveal_node(idx)
                reveal["node_i"] += 1
        elif reveal["edge_i"] < len(edges):
            if reveal["frame"] % REVEAL_FRAMES_PER_EDGE == 0:
                reveal["edge_i"] += 1
                shown = reveal["edge_order"][:reveal["edge_i"]]
                revealed_edge_parent = parent_idx[shown]
                revealed_edge_child = child_idx[shown]
        else:
            reveal["active"] = False

    def reveal_all_immediately():
        nonlocal revealed_edge_parent, revealed_edge_child
        reveal.update(active=False, node_i=n, edge_i=len(edges))
        for i in range(n):
            reveal_node(i)
        revealed_edge_parent = parent_idx
        revealed_edge_child = child_idx

    # ---------------------------------------------------------
    #  ФИЗИКА (векторизовано на numpy)
    #
    #  Раньше отталкивание считалось как полная матрица n x n на каждый
    #  кадр (diff = pos[:, None, :] - pos[None, :, :]) - то есть КАЖДЫЙ
    #  узел отталкивался от КАЖДОГО, даже от тех, что за пределами экрана.
    #  При росте числа фредиков это растёт квадратично и именно это душило
    #  анимацию. Теперь через KD-дерево (scipy) находим только пары узлов
    #  ближе REPULSION_CUTOFF друг к другу - дальние пары дают исчезающе
    #  малую силу и на глаз результат не отличается, а считается на порядок
    #  быстрее. Если scipy не установлен - используется старый честный
    #  способ как запасной вариант.
    # ---------------------------------------------------------
    def compute_forces():
        forces = np.zeros((n, 2))

        if _HAS_SCIPY and n > 1:
            tree = cKDTree(pos)
            pairs = tree.query_pairs(r=REPULSION_CUTOFF, output_type="ndarray")
            if len(pairs):
                i_idx, j_idx = pairs[:, 0], pairs[:, 1]
                diff = pos[i_idx] - pos[j_idx]
                dist_sq = np.einsum("ij,ij->i", diff, diff)
                dist_sq = np.where(dist_sq < 1e-6, 1e-6, dist_sq)
                dist = np.sqrt(dist_sq)
                repel = params["repulsion"] / dist_sq
                fx = diff[:, 0] / dist * repel
                fy = diff[:, 1] / dist * repel
                np.add.at(forces[:, 0], i_idx, fx)
                np.add.at(forces[:, 1], i_idx, fy)
                np.add.at(forces[:, 0], j_idx, -fx)
                np.add.at(forces[:, 1], j_idx, -fy)
        else:
            diff = pos[:, None, :] - pos[None, :, :]
            dist_sq = np.sum(diff * diff, axis=-1)
            np.fill_diagonal(dist_sq, np.inf)
            dist = np.sqrt(dist_sq)
            dist_safe = np.where(dist < 1e-3, 1e-3, dist)
            repel = params["repulsion"] / np.where(dist_sq < 1e-6, 1e-6, dist_sq)
            forces[:, 0] = np.sum(diff[..., 0] / dist_safe * repel, axis=1)
            forces[:, 1] = np.sum(diff[..., 1] / dist_safe * repel, axis=1)

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

        # Тяги к поколению больше нет - раньше она держала каждый узел
        # "привязанным" к своей горизонтальной линии, из-за чего верхнее и
        # нижнее поколения не могли свободно разойтись и вели себя как будто
        # упирались в невидимую стену с пружиной. Теперь по вертикали узлы
        # свободны и расходятся только под действием отталкивания и связей.
        forces[:, 0] += -pos[:, 0] * params["center_pull"]
        if params["jitter"] > 0:
            forces += np.random.uniform(-params["jitter"], params["jitter"], size=(n, 2))
        return forces

    def step_physics():
        forces = compute_forces()
        free = ~dragged_mask
        dt = params["dt"]
        vel[free] = (vel[free] + forces[free] * dt) * params["damping"]
        pos[free] += vel[free] * dt

    # ---------------------------------------------------------
    #  ОБНОВЛЕНИЕ ПОЗИЦИЙ У УЖЕ СУЩЕСТВУЮЩИХ ARTIST'ОВ
    # ---------------------------------------------------------
    def update_artists():
        for i in range(n):
            x, y = pos[i]
            if halo_circles[i].get_visible():
                halo_circles[i].center = (x, y)
            im = images[i]
            if im is not None and im.get_visible():
                hw, hh = half_sizes[i]
                im.set_extent((x - hw, x + hw, y - hh, y + hh))
            dot = fallback_dots[i]
            if dot is not None and dot.get_visible():
                dot.center = (x, y)
                dot.set_edgecolor(ACCENT_COLOR if dragged_idx["i"] == i else "#ffffff")
                dot.set_linewidth(2.4 if dragged_idx["i"] == i else 1.1)
            if name_texts[i].get_visible():
                name_texts[i].set_position((x, y + NODE_IMG_HALF + 0.14))
            if gen_texts[i].get_visible():
                gen_texts[i].set_position((x, y - NODE_IMG_HALF - 0.14))
            if dragged_idx["i"] == i and halo_circles[i].get_visible():
                halo_circles[i].set_edgecolor(ACCENT_COLOR)
                halo_circles[i].set_linewidth(2.0)
            elif halo_circles[i].get_visible():
                halo_circles[i].set_linewidth(0)

        _update_edges_and_arrows()

    def _update_edges_and_arrows():
        if len(revealed_edge_parent) == 0:
            edge_collection.set_segments([])
            arrow_collection.set_segments([])
            return

        p = pos[revealed_edge_parent]
        c = pos[revealed_edge_child]
        vec = c - p
        dist = np.hypot(vec[:, 0], vec[:, 1])
        dist_safe = np.where(dist < 1e-6, 1e-6, dist)
        unit = vec / dist_safe[:, None]

        start = p + unit * EDGE_SHRINK
        end = c - unit * EDGE_SHRINK
        segs = np.stack([start, end], axis=1)
        edge_collection.set_segments(segs)

        # наконечник-стрелка ("шеврон") прямо перед узлом-ребёнком
        angle = np.arctan2(unit[:, 1], unit[:, 0])
        spread = np.radians(ARROW_WIDTH_DEG)
        tip = end
        left = tip - ARROW_LEN * np.stack([np.cos(angle - spread), np.sin(angle - spread)], axis=1)
        right = tip - ARROW_LEN * np.stack([np.cos(angle + spread), np.sin(angle + spread)], axis=1)

        arrow_segs = np.stack([left, tip, right], axis=1)
        arrow_collection.set_segments(arrow_segs)

    # ---------------------------------------------------------
    #  НАВЕДЕНИЕ МЫШЬЮ - ПОДСКАЗКА СО СТАТИСТИКОЙ
    # ---------------------------------------------------------
    def find_node(x, y):
        if x is None or y is None:
            return None
        dist = np.hypot(pos[:, 0] - x, pos[:, 1] - y)
        i = int(np.argmin(dist))
        return i if dist[i] < HIT_RADIUS else None

    def tooltip_text(node):
        gender = GENDER_LABELS.get(node.gender, node.gender)
        status = "жив" if node.alive else "мёртв"
        return (
            f"{node.name}\n"
            f"Статус: {status}\n"
            f"Поколение: {node.generation}\n"
            f"Возраст: {node.age}\n"
            f"Пол: {gender}\n"
            f"Редкость: {node.rarity}\n"
            f"GenID/GenDom: {node.genid}/{node.gendom}\n"
            f"Мутация: {node.mutrate}%"
        )

    def update_hover(i):
        if hover_state["i"] == i:
            if i is not None:
                x, y = pos[i]
                tooltip.xy = (x, y)
            return
        hover_state["i"] = i
        if i is None:
            tooltip.set_visible(False)
        else:
            node = nodes[i]
            tooltip.set_text(tooltip_text(node))
            x, y = pos[i]
            tooltip.xy = (x, y)
            tooltip.set_visible(True)
        fig.canvas.draw_idle()

    # ---------------------------------------------------------
    #  СОН / ПРОБУЖДЕНИЕ АНИМАЦИИ
    # ---------------------------------------------------------
    sleep_state = {"asleep": False, "quiet_frames": 0}
    anim_ref = {}

    def wake():
        sleep_state["quiet_frames"] = 0
        if sleep_state["asleep"]:
            sleep_state["asleep"] = False
            anim = anim_ref.get("anim")
            if anim is not None:
                anim.event_source.start()

    # ---------------------------------------------------------
    #  ПЕРЕТАСКИВАНИЕ УЗЛОВ + ПАНОРАМИРОВАНИЕ ПОЛЯ + ЗУМ КОЛЁСИКОМ
    # ---------------------------------------------------------
    pan_state = {"active": False, "start_px": None, "start_xlim": None, "start_ylim": None}

    def on_press(event):
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            return
        i = find_node(event.xdata, event.ydata)
        dragged_idx["i"] = i
        if i is not None:
            dragged_mask[i] = True
            vel[i] = 0.0
            wake()
        else:
            # клик по пустому месту - тащим саму сцену (панорама)
            pan_state.update(active=True, start_px=(event.x, event.y),
                             start_xlim=ax.get_xlim(), start_ylim=ax.get_ylim())
            update_hover(None)

    def on_motion(event):
        i = dragged_idx["i"]
        if i is not None:
            if event.inaxes == ax and event.xdata is not None and event.ydata is not None:
                pos[i] = (event.xdata, event.ydata)
            return

        if pan_state["active"]:
            if event.x is None or event.y is None:
                return
            dx_px = event.x - pan_state["start_px"][0]
            dy_px = event.y - pan_state["start_px"][1]
            bbox = ax.get_window_extent()
            if bbox.width <= 0 or bbox.height <= 0:
                return
            xlim0, ylim0 = pan_state["start_xlim"], pan_state["start_ylim"]
            dx_data = -dx_px / bbox.width * (xlim0[1] - xlim0[0])
            dy_data = -dy_px / bbox.height * (ylim0[1] - ylim0[0])
            ax.set_xlim(xlim0[0] + dx_data, xlim0[1] + dx_data)
            ax.set_ylim(ylim0[0] + dy_data, ylim0[1] + dy_data)
            fig.canvas.draw_idle()
            return

        if event.inaxes != ax:
            update_hover(None)
            return
        update_hover(find_node(event.xdata, event.ydata))

    def on_release(event):
        i = dragged_idx["i"]
        if i is not None:
            dragged_mask[i] = False
        dragged_idx["i"] = None
        pan_state["active"] = False

    def on_scroll(event):
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            return
        step = getattr(event, "step", 0)
        zooming_in = (step > 0) if step else (event.button == "up")
        factor = ZOOM_IN_FACTOR if zooming_in else ZOOM_OUT_FACTOR

        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        span_x = (cur_xlim[1] - cur_xlim[0]) * factor
        span_y = (cur_ylim[1] - cur_ylim[0]) * factor

        home_span_x = home_xlim[1] - home_xlim[0]
        min_span_x = MIN_VIEW_SPAN
        max_span_x = home_span_x * MAX_VIEW_ZOOM_OUT
        if not (min_span_x <= span_x <= max_span_x):
            return

        xdata, ydata = event.xdata, event.ydata
        relx = (xdata - cur_xlim[0]) / (cur_xlim[1] - cur_xlim[0])
        rely = (ydata - cur_ylim[0]) / (cur_ylim[1] - cur_ylim[0])
        ax.set_xlim(xdata - span_x * relx, xdata + span_x * (1 - relx))
        ax.set_ylim(ydata - span_y * rely, ydata + span_y * (1 - rely))
        wake()
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("motion_notify_event", on_motion)
    fig.canvas.mpl_connect("button_release_event", on_release)
    fig.canvas.mpl_connect("scroll_event", on_scroll)

    # ---------------------------------------------------------
    #  КНОПКА "ПЕРЕСОБРАТЬ"
    # ---------------------------------------------------------
    def regenerate(event):
        layout_by_generation(params["spring_len"], 0.5, 0.4)
        prev_pos[:] = pos
        vel[:] = np.random.uniform(-0.6, 0.6, size=(n, 2))
        ax.set_xlim(*home_xlim)
        ax.set_ylim(*home_ylim)
        start_reveal()
        wake()

    button_ax = fig.add_axes([0.77, 0.015, 0.2, 0.055])
    button_ax.set_facecolor(PANEL_COLOR)
    regenerate_button = Button(button_ax, "⟳ Пересобрать", color=PANEL_COLOR, hovercolor=PANEL_HOVER)
    regenerate_button.label.set_color(TEXT_COLOR)
    regenerate_button.label.set_fontsize(10)
    regenerate_button.on_clicked(regenerate)

    # ---------------------------------------------------------
    #  ВЫЕЗЖАЮЩАЯ ПАНЕЛЬ НАСТРОЕК
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

    slider_axes_info = []
    label_texts_info = []
    sliders = []

    row_top = PANEL_BOTTOM + PANEL_HEIGHT_FRAC - 0.11
    row_gap = 0.075
    row_h = 0.026

    def update_param(key, val):
        params[key] = val
        wake()

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

    def do_reset(event):
        for s in sliders:
            s.reset()
        wake()

    reset_button.on_clicked(do_reset)

    def sync_panel_positions():
        delta = panel_state["x"] - PANEL_OPEN_X
        panel_bg_ax.set_position([PANEL_OPEN_X + delta, PANEL_BOTTOM, PANEL_WIDTH, PANEL_HEIGHT_FRAC])
        title_text.set_position((title_open_x + delta, title_y))
        for ax_s, open_x, y, w, h in slider_axes_info:
            ax_s.set_position([open_x + delta, y, w, h])
        for txt, open_x, y in label_texts_info:
            txt.set_position((open_x + delta, y))
        reset_button_ax.set_position([reset_open_x + delta, reset_y, reset_w, reset_h])

    sync_panel_positions()

    def toggle_panel(event):
        panel_state["open"] = not panel_state["open"]
        panel_state["target_x"] = PANEL_OPEN_X if panel_state["open"] else PANEL_CLOSED_X
        wake()

    gear_button_ax = fig.add_axes([0.955, 0.925, 0.038, 0.05])
    gear_button = Button(gear_button_ax, "⚙", color=PANEL_COLOR, hovercolor=PANEL_HOVER)
    gear_button.label.set_color(TEXT_COLOR)
    gear_button.label.set_fontsize(13)
    gear_button.on_clicked(toggle_panel)

    # ---------------------------------------------------------
    #  КНОПКА "НА ДОМ" - сбросить панораму/зум, если фредики разбежались
    # ---------------------------------------------------------
    def go_home(event):
        ax.set_xlim(*home_xlim)
        ax.set_ylim(*home_ylim)
        wake()
        fig.canvas.draw_idle()

    home_button_ax = fig.add_axes([0.015, 0.015, 0.09, 0.05])
    home_button = Button(home_button_ax, "⌂ Вид", color=PANEL_COLOR, hovercolor=PANEL_HOVER)
    home_button.label.set_color(TEXT_COLOR)
    home_button.label.set_fontsize(10)
    home_button.on_clicked(go_home)

    # ---------------------------------------------------------
    #  ЦИКЛ АНИМАЦИИ
    # ---------------------------------------------------------
    def animate(frame):
        prev_pos[:] = pos
        step_physics()
        advance_reveal()
        update_artists()

        panel_moving = panel_state["x"] != panel_state["target_x"]
        if panel_moving:
            panel_state["x"] += (panel_state["target_x"] - panel_state["x"]) * PANEL_EASE
            if abs(panel_state["target_x"] - panel_state["x"]) < 0.0015:
                panel_state["x"] = panel_state["target_x"]
            sync_panel_positions()

        max_move = np.max(np.hypot(*(pos - prev_pos).T)) if n else 0.0
        busy = reveal["active"] or panel_moving or dragged_idx["i"] is not None or pan_state["active"]
        if not busy and max_move < SLEEP_MOVE_EPS:
            sleep_state["quiet_frames"] += 1
            if sleep_state["quiet_frames"] >= SLEEP_FRAMES_NEEDED:
                sleep_state["asleep"] = True
                anim_ref["anim"].event_source.stop()
        else:
            sleep_state["quiet_frames"] = 0

        return []

    reveal_all_immediately()
    update_artists()
    anim = FuncAnimation(fig, animate, interval=FRAME_INTERVAL_MS, cache_frame_data=False)
    anim_ref["anim"] = anim
    fig._tree_animation_ref = anim

    regenerate(None)

    plt.show()
