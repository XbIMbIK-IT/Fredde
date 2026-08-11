import networkx as nx 
from fredde import freddis
import matplotlib.pyplot as plt

def show():
	G = nx.Graph()

	for f in freddis:
		G.add_node(f.name)

	plt.figure(figsize=(8, 6))
	nx.draw(G)
	plt.show()