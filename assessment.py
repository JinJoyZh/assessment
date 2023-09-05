import networkx as nx
import numpy as np
import random
from pyvis.network import Network
import pandas as pd
# Define the number of nodes and edges
num_nodes = 20
num_edges = 200

# Define the node types and edge types
node_types = ['S', 'P', 'C', 'T']
edge_types = ['C_to_C', 'S_to_S', 'T_to_T', 'P_to_P',
              'S_to_C', 'C_to_P', 'P_to_C', 'C_to_T']
## 问题1：是否可以把同类型间链接和不同类型之间链接区别开？
## 问题2：'C_to_C':'通信协同、接替、备份' 存在多种不同的关系，如何表示？ 设计三种'C_to_C1', 'C_to_C2', 'C_to_C3'？
edge_labels = {'C_to_C':'通信协同、接替、备份','S_to_S':'侦察协同', 'T_to_T':'打击协同', 'P_to_P':'指控协同',
               'S_to_C':'信息上报', 'C_to_P':'通信关系', 'P_to_C':'通信关系', 'C_to_T':'指控关系'}
node_labels = {'S':'侦察节点',
                'P':'指控节点',
                'C':'通信节点',
                'T':'打击节点'}


# Define allowed connections for each node type with 80% probability
allowed_connections = {
    'S': ['S','C'],
    'P': ['P', 'C'],
    'C': ['C', 'P', 'T'],
    'T': ['T']
}

# Define colors for each node type and edge type
node_colors_dict = {'S': 'red', 'P': 'green', 'C': 'blue', 'T': 'yellow'}
edge_colors_dict = {'C_to_C': 'red', 'S_to_S': 'yellow', 'T_to_T': 'black','P_to_P': 'green', 
                    'S_to_C': 'pink', 'C_to_P': 'orange', 'P_to_C': 'blue','C_to_T':'purple'}
                    # 'unknown': 'black'}
colors_HEX_dict={'red':'#FF0000',
                 'green': '#008000',
                 'blue': '#0000FF',
                 'yellow':'#FFFF00',
                 'purple':'#800080',
                 'pink':'#FFC0CB', 
                 'orange':'#FFA500', 
                 'black':'#000000'}
# Randomly assign types to the nodes
node_type_assignments = random.choices(node_types, k=num_nodes)

# Create the graph
G = nx.DiGraph()

# Add nodes to the graph with their types
for i in range(num_nodes):
    G.add_node(i, node_type=node_type_assignments[i],
        color=colors_HEX_dict[node_colors_dict[node_type_assignments[i]]],
        label=str(i))

# Add edges to the graph
for i in range(num_edges):
    source = random.randint(0, num_nodes-1)
    source_type = G.nodes[source]['node_type']

    # Decide if we're following the allowed connections (80% chance) or connecting randomly (20% chance)
    if random.random() < 0.8:
        # Follow the allowed connections
        target_type = random.choice(allowed_connections[source_type])
        possible_targets = [n for n in G.nodes() if G.nodes[n]['node_type'] == target_type]
        if not possible_targets:  # If no possible targets of required type, connect randomly
            target = random.randint(0, num_nodes-1)
        else:
            target = random.choice(possible_targets)
    else:
        # Connect randomly
        target = random.randint(0, num_nodes-1)

    edge_type = source_type + '_to_' + G.nodes[target]['node_type']
    if edge_type not in edge_types:
        continue
        edge_type = 'unknown'
    G.add_edge(source, target, edge_type=edge_type,color=colors_HEX_dict[edge_colors_dict[edge_type]],label=edge_labels[edge_type])

# Define the color map for the nodes
node_colors = [node_colors_dict[G.nodes[node]['node_type']] for node in G.nodes()]
# Define the color map for the edges
edge_colors = [edge_colors_dict[G.edges[edge]['edge_type']] for edge in G.edges()]


# 图例
for i in range(len(node_types)):
    G.add_node(i+num_nodes,node_type=node_types[i], 
        color=colors_HEX_dict[node_colors_dict[node_types[i]]],
        label=node_types[i]+'：'+node_labels[node_types[i]],x=-700,y=-300+i*60,shape='box',
        size=20,widthConstraint=100, font={'size': 20},physics=False)
    
for i in range(len(edge_types)):
    G.add_node(i+num_nodes+len(node_types),node_type=edge_types[i], 
        color=colors_HEX_dict[edge_colors_dict[edge_types[i]]],
        label=edge_types[i]+'：'+edge_labels[edge_types[i]],x=700,y=-300+i*60,shape='box',
        size=20,widthConstraint=200, font={'size': 20},physics=False)


# 建图、保存
G_vis = Network(1080,1920, directed=True)
G_vis.repulsion()
G_vis.from_nx(G)
G_vis.toggle_stabilization(True)
G_vis.toggle_hide_edges_on_drag(True) # 拖动节点时隐藏边

G_vis.show_buttons(filter_=['physics'])
G_vis.show('demo.html',notebook=False)



print(G)
print("1 节点数", len(G.nodes))
print("2 边数", len(G.edges))
print("6 平均度：", sum(dict(nx.degree(G)).values())/len(G.nodes))
print("8 平均集聚系数", nx.average_clustering(G))


try:
    print("9 平均最短路径", nx.average_shortest_path_length(G))
    print("10 网络平均效率", 1/nx.average_shortest_path_length(G))
except:
    print('非强连接图，无法计算平均最短路径与网络平均效率')
print("12 链路节点比", len(G.edges)/len(G.nodes))
