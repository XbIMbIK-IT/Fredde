import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.widgets import Button

from fredde import freddis


def show():
    G = nx.DiGraph()

    for f in freddis:
        G.add_node(f)

    for child in freddis:
        for parent in child.parents:
            G.add_edge(parent, child)

    if not G.nodes:
        print("Генеалогическое дерево пустое.")
        return

    pos = nx.spring_layout(
        G,
        k=2.5,
        iterations=300
    )

    fig, ax = plt.subplots(figsize=(12, 8))
    plt.subplots_adjust(bottom=0.12)

    dragged_node = {"node": None}

    def draw_graph():
        ax.clear()

        node_colors = [
            tuple(max(0, min(255, c)) / 255 for c in node.color[:3])
            for node in G.nodes
        ]

        nx.draw_networkx_edges(
            G,
            pos,
            ax=ax,
            edge_color="gray",
            width=1.5,
            alpha=0.7,
            arrows=True,
            arrowsize=15,
            arrowstyle="-|>"
        )

        nx.draw_networkx_nodes(
            G,
            pos,
            ax=ax,
            node_color=node_colors,
            node_size=1800,
            node_shape="o",
            edgecolors="black",
            linewidths=1.5
        )

        labels = {
            node: node.name
            for node in G.nodes
        }

        nx.draw_networkx_labels(
            G,
            pos,
            labels=labels,
            ax=ax,
            font_size=9,
            font_weight="bold"
        )

        ax.set_title("Генеалогическое древо")
        ax.set_axis_off()

        fig.canvas.draw_idle()

    def find_node(x, y):
        if x is None or y is None:
            return None

        threshold = 0.08

        closest_node = None
        closest_distance = float("inf")

        for node, (nx_pos, ny_pos) in pos.items():
            distance = (
                (nx_pos - x) ** 2 +
                (ny_pos - y) ** 2
            ) ** 0.5

            if distance < threshold and distance < closest_distance:
                closest_distance = distance
                closest_node = node

        return closest_node

    def on_press(event):
        if event.inaxes != ax:
            return

        if event.xdata is None or event.ydata is None:
            return

        dragged_node["node"] = find_node(
            event.xdata,
            event.ydata
        )

    def on_motion(event):
        node = dragged_node["node"]

        if node is None:
            return

        if event.inaxes != ax:
            return

        if event.xdata is None or event.ydata is None:
            return

        pos[node] = (
            event.xdata,
            event.ydata
        )

        draw_graph()

    def on_release(event):
        dragged_node["node"] = None

    def regenerate(event):
        nonlocal pos

        pos = nx.spring_layout(
            G,
            k=2.5,
            iterations=300
        )

        draw_graph()

    button_ax = fig.add_axes(
        [0.78, 0.02, 0.17, 0.055]
    )

    regenerate_button = Button(
        button_ax,
        "Перегенерировать"
    )

    regenerate_button.on_clicked(regenerate)

    fig.canvas.mpl_connect(
        "button_press_event",
        on_press
    )

    fig.canvas.mpl_connect(
        "motion_notify_event",
        on_motion
    )

    fig.canvas.mpl_connect(
        "button_release_event",
        on_release
    )

    draw_graph()

    plt.show()
