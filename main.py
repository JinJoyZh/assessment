
import collections
import json
from flask import Flask, jsonify, request
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt


from louvain import Louvain


server = Flask(__name__)

EDGE_WEIGHTS = {
    "C_to_C": np.ones(1),   #edge类型为 通信协同、接替、备份 的权重值
    "T_to_T": np.ones(1),   #edge类型为 打击协同  的权重值
    "P_to_C": np.ones(1),   #edge类型为 通信关系  的权重值
    "S_to_S": np.ones(1),   #edge类型为 侦查协同  的权重值
    "T_to_T": np.ones(1),   #edge类型为 打击协同  的权重值
    "S_to_C": np.ones(1),   #edge类型为 信息上报  的权重值
    "C_to_T": np.ones(1),   #edge类型为 指控关系  的权重值
    "C_to_P": np.ones(1),   #edge类型为 通信关系  的权重值
    "P_to_P": np.ones(1)    #edge类型为 指控协同  的权重值
}

@server.route('/assess', methods=['POST'])
def on_receive_data():
    try:
        msg = request.get_json()
        print(msg)
    except Exception as e:
        print(e)
        return jsonify({'error': '请求失败'}), 400
    
    global result
    if msg:
        try:
            result = process_data(msg)
        except Exception as e:
            return jsonify({'error': '处理数据失败'}), 666
    if not result:
        result = 'error'
    return result

#构造网络
def construct_graph(edge_json):#输入初始文件的路径，构造一个有起点、终点、边权的网络
    G=collections.defaultdict(dict)#设置空白默认字典
    for edge in edge_json:
        v_i=int(edge["source_node_id"])
        v_j=int(edge["target_node_id"])
        edge_type = edge["edge_type"]
        w = EDGE_WEIGHTS[edge_type]
        G[v_i][v_j]=w
        G[v_j][v_i]=w
    return G

def process_data(msg):
    # edge.json is used for test
    with open("data/edge.json",'r') as load_f:
        msg = json.load(load_f)
    G = construct_graph(msg)
    algorithm = Louvain(G)
    communities = algorithm.execute() #集群结构       
    #计算基础指标
    G=nx.to_networkx_graph(G)
    node_num = len(G.nodes)                                                 # 1 节点数      
    edge_num = len(G.edges)                                                 # 2 度
    degree = sum(dict(nx.degree(G)).values())/len(G.nodes)                  # 6 平均度
    clustering_coefficient = nx.average_clustering(G)                       # 8 平均集聚系数 - 由集群数量和规模决定
    average_shortest_path_length = 0
    average_network_efficiency = 0
    try:
        average_shortest_path_length = nx.average_shortest_path_length(G)   # 9 平均最短路径
        average_network_efficiency = 1/nx.average_shortest_path_length(G)   # 10 网络平均效率 ｜ 介数
    except:
        print('非强连接图，无法计算平均最短路径与网络平均效率')
    link_node_ratio = len(G.edges)/len(G.nodes)                             # 12 链路节点比
    A = np.array(nx.adjacency_matrix(G).todense())  # 从图G中获取邻接矩阵
    eigenvalue, _ = np.linalg.eig(A)  # 求解特征值
    cne = np.max(eigenvalue) / node_num                                     # 13 散度
    contivity = nx.number_connected_components(G)                           # 14 连通度

    #计算能力效果 （忽略 网络重心分布及数量/中立率的影响）
    # a 抗毁性  根据 （网络重心分布及数量）/连通度/节点链路比/介数 计算
    invulnerability = 0.33 * contivity + 0.33 * link_node_ratio + 0.33 * average_network_efficiency
    # b 重组性  根据 (网络重心分布及数量)/连通度 计算                                          
    recombination = contivity
    # c 分散性  根据 (网络重心分布及数量)/介数/集群数量和规模 计算                                             
    dispersion = 0.5 * clustering_coefficient + 0.5 * average_network_efficiency 
    # d 隐蔽性  根据 集群数量和规模/散度 计算                                         
    concealment = 0.5 * clustering_coefficient + 0.5 * cne   
    # e 邻近性  根据 节点数量/(网络重心分布及数量)/集群数量和规模 计算                                      
    proximity = 0.5 * node_num + 0.5 * clustering_coefficient              
    # f 灵活性  根据 度/连通度 计算          
    flexibility = 0.5 * edge_num + 0.5 * contivity                          
    # g 适应性  根据 度/连通度/介数/(中立率) 计算                   
    adaptability = 0.33 * edge_num + 0.33 * contivity + 0.33 * average_network_efficiency         
    # h 高效性  根据 (网络重心分布及数量)/介数/连通度 计算                                               
    efficiency = 0.5 * average_network_efficiency + 0.5 * contivity                                                
    return {"抗毁性": invulnerability,
            "重组性": recombination,
            "分散性": dispersion,
            "隐蔽性": concealment,
            "邻近性": proximity,
            "灵活性": flexibility,
            "适应性": adaptability,
            "高效性": efficiency
            }              

if __name__ == '__main__':
    server.run()