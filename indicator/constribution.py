import time
import networkx as nx
import matplotlib.pyplot as plt
import random

def compute_contribution(G, node):
    # 计算节点的传播能力
    prop_ability = nx.in_degree_centrality(G)[node]

    # 计算节点的体系贡献率
    contributions = []
    for n in G.nodes():
        if n != node:
            try:
                simple_paths = nx.all_simple_paths(G, node, n)
                path_lengths = [len(path) - 1 for path in simple_paths]
                node_count = G.degree(node)
                path_count = sum([1 for length in path_lengths if length == node_count])
                contribution = path_count / node_count
                contributions.append(contribution)
            except nx.NetworkXNoPath:
                continue

    if len(contributions) == 0:
        avg_contribution = 0
    else:
        avg_contribution = sum(contributions) / len(contributions)

    # 考虑节点的度中心性，将传播能力和体系贡献率相乘
    total_contribution = prop_ability * avg_contribution

    # 返回节点的传播能力、体系贡献率和综合贡献率
    return prop_ability, avg_contribution, total_contribution

def identify_critical_nodes(G, threshold):
    critical_marks = []
    contribution_list = []
    for node in G.nodes():
        prop_ability, avg_contribution, total_contribution = compute_contribution(G, node)
        if total_contribution > threshold:
            critical_marks.append(1)
            contribution_list.append(total_contribution)
        else:
            critical_marks.append(0)
            contribution_list.append(0.0)
    return critical_marks, contribution_list

# # 创建一个图并添加节点和边
# G = nx.DiGraph()
# num_nodes = 50
# nodes = [str(i) for i in range(num_nodes)]
# G.add_nodes_from(nodes)
# for i in range(num_nodes):
#     for j in range(i + 1, num_nodes):
#         if random.random() < 0.2:  # 随机生成边
#             G.add_edge(str(i), str(j))

# # 设置综合贡献率的阈值
# threshold = 0.0

# # 识别关键节点
# critical_nodes, contribution_list = identify_critical_nodes(G, threshold)

# # 绘制图形
# pos = nx.spring_layout(G, seed=1)  # 设置节点布局，seed是为了使布局相对稳定
# nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=200)  # 绘制所有节点
# nx.draw_networkx_nodes(G, pos, nodelist=critical_nodes, node_color='red', node_size=200)  # 绘制关键节点
# nx.draw_networkx_edges(G, pos, edge_color='gray')  # 绘制边
# nx.draw_networkx_labels(G, pos, font_color='black')  # 绘制节点标签

# plt.axis('off')  # 关闭坐标轴
# plt.title('Critical Nodes Visualization')  # 设置标题
# plt.show()  # 显示图形

# print("关键节点列表：", critical_nodes)
# print("关键节点贡献度：", contribution_list)  # 需要把贡献度排序画个图展示出来