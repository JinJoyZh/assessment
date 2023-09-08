
import collections
import numpy as np
import networkx as nx


from louvain import Louvain


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

#构造网络
def construct_graph(edge_json):#输入初始文件的路径，构造一个有起点、终点、边权的网络
    G=collections.defaultdict(dict)#设置空白默认字典
    for edge in edge_json:
        v_i=int(edge["source"])
        v_j=int(edge["target"])
        # edge_type = edge["edge_type"]
        w = np.ones(1)
        G[v_i][v_j]=w
        G[v_j][v_i]=w
    return G

def process_data(msg):
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
    return {
            "抗毁性": invulnerability,
            "重组性": recombination,
            "分散性": dispersion,
            "隐蔽性": concealment,
            "邻近性": proximity,
            "灵活性": flexibility,
            "适应性": adaptability,
            "高效性": efficiency
            }              
