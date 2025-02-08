import copy
import time
import tsplib95 
import math

def calcula_matriz_distancia(problema):
    
    # DIMENSION = quantidade de vértices do problema (incluindo depot)
    n = problema.dimension
    coords = problema.node_coords # dicionário com todas as coordenadas

    # O arquivo-problema indexa usando 1, e não 0
    distancias = [[0]*(n+1) for _ in range(n+1)]

    # Para cada vértice
    for i in range(1, n+1):
        # Calcula a distância dele para todos os outros
        for j in range(1, n+1):
            xi, yi = coords[i]
            xj, yj = coords[j]

            # Eleva cada elemento ao quadrado, soma, e tira a raíz quadrada do resultado
            d = math.hypot(xi - xj, yi - yj) # Existe uma função pra isso! :O

            distancias[i][j] = d
            distancias[j][i] = d

    return distancias

def solucao_inicial(problema, dist):
    # De novo, o arquivo indexa começando em 1.
    nao_visitado = set(range(1, problema.dimension+1))
    depot = problema.depots[0]

    # Agora temos só os vértices dos clientes
    nao_visitado.discard(depot)

    rotas = []
    # Cria as rotas
    while nao_visitado:
        rota = [depot]
        carga = 0
        atual = depot

        # Adiciona os vértices na rota
        while True:
            melhor_d = float("inf")
            melhor_vizinho = None

            # Nessa construção inicial, o algoritmo guloso considera todo mundo um vizinho
            for vizinho in list(nao_visitado):
                if (carga + problema.demands[vizinho] < problema.capacity):
                    if (dist[atual][vizinho] < melhor_d):
                        melhor_d = dist[atual][vizinho]
                        melhor_vizinho = vizinho

            if melhor_vizinho is None:
                break

            rota.append(melhor_vizinho)
            carga += problema.demands[melhor_vizinho]
            nao_visitado.remove(melhor_vizinho)

            atual = melhor_vizinho

        rota.append(depot)
        rotas.append(rota)

    return rotas

def ILS(problema, dist, maximo_segundos, tamanho_perturbacao):
    tempo_inicial = time.time()

    solucao_atual = solucao_inicial(problema, dist)
    solucao_atual = busca_local(solucao_atual)
    melhor_solucao = copy.deepcopy(solucao_atual)

    while time.time() - tempo_inicial < maximo_segundos:

        solucao_candidata, removidas = remocao_arestas(solucao_atual, tamanho_perturbacao)
        solucao_candidata = reinsercao_arestas(solucao_candidata, removidas, problema, dist)
        solucao_candidata = busca_local(solucao_candidata)
        custo_candidata = custo_total(solucao_atual, dist)

        if custo_candidata < custo_total(solucao_atual, dist):
            solucao_atual = copy.deepcopy(custo_candidata)

        if custo_candidata < custo_total(melhor_solucao):
            melhor_solucao = copy.deepcopy(solucao_atual)

def busca_local(solucao_referencia):
    

def main():
    arquivo = "instancias/A/A-n32-k5.vrp"
    problema = tsplib95.load(arquivo)

    dist = calcula_matriz_distancia(problema)
   
    test = solucao_inicial(problema, dist)

    print(test)

    #melhor_solucao, melhor_custo = ILS(problema, dist, maximo_segundos=300, tamanho_perturbacao=3)


    
main()

# Testar a matriz distância
# test = [ [ str(int(e)).zfill(3) for e in l] for l in matriz_distancia]

# with open("out.txt", "w") as f:
#     print(test, file=f)
