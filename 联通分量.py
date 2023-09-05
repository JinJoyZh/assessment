def dfs(graph, visited, vertex):
    visited[vertex] = True
    print(vertex, end=" ")

    for neighbor in graph[vertex]:
        if not visited[neighbor]:
            dfs(graph, visited, neighbor)

def find_connected_components(graph):
    num_vertices = len(graph)
    visited = [False] * num_vertices

    for vertex in range(num_vertices):
        if not visited[vertex]:
            dfs(graph, visited, vertex)
            print()

# 示例图
graph = {
    0: [1, 2],
    1: [0, 2],
    2: [0, 1],
    3: [4],
    4: [3]
}

find_connected_components(graph)