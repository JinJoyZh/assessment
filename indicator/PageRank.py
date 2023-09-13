import networkx as nx
import matplotlib.pyplot as plt

# 创建有标度网络
N = 1000
m = 4
p = 0.2
ws_graph = nx.watts_strogatz_graph(N, m, p, seed=1)

# 计算节点的PageRank值
pr = nx.pagerank(ws_graph, alpha=0.9)

# 排序输出PageRank值最高的k个节点
k = 10
top_k = sorted(pr.items(), key=lambda x: x[1], reverse=True)[:k]
print("PageRank Top-k nodes:")
for node, value in top_k:
    print("Node: {}, PageRank value: {}".format(node, value))  # 需要把节点重要度排序画个图展示出来

# 可视化有标度网络
# nx.draw(ws_graph, node_size=20, node_color='skyblue', alpha=0.8, with_labels=False)
# plt.title("Visualization of the Scale-free Network")
# plt.show()