import copy
import random
import time
import tsplib95
import math
import bisect

def calcula_matrizes(problema, quantidade_vizinhos):
    
    # DIMENSION = quantidade de vértices do problema (incluindo depot)
    n = problema.dimension
    coords = problema.node_coords # dicionário com todas as coordenadas

    # O arquivo-problema indexa usando 1, e não 0
    distancias = [[0]*(n+1) for _ in range(n+1)]
    todos_vizinhos = {}

    # Para cada vértice
    for i in range(1, n+1):
        vizinhos = []
        # Calcula a distância dele para todos os outros
        for j in range(1, n+1):
            xi, yi = coords[i]
            xj, yj = coords[j]

            # Eleva cada elemento ao quadrado, soma, e tira a raíz quadrada do resultado
            d = math.hypot(xi - xj, yi - yj) # Existe uma função pra isso! :O

            distancias[i][j] = d
            distancias[j][i] = d

            if len(vizinhos) < quantidade_vizinhos or d < vizinhos[-1]:
                bisect.insort(vizinhos, j)

                if len(vizinhos) > quantidade_vizinhos: 
                    vizinhos.pop()

        todos_vizinhos[i] = vizinhos

    return distancias, todos_vizinhos

def gera_solucao_inicial(problema, dist):
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

def custo(solucao, dist):
    soma = 0
    for rota in solucao:
        # Para o primeiro vértice (depot) funcionar no loop
        previous = rota[0]
        for vertice in rota:
            soma += dist[previous][vertice]
            previous = vertice

    return soma

def reinsercao_vertice(solucao_candidata, removido, problema, dist, rota_removido=None, idx_removido=None, precisa_ser_viavel=False):
    melhor_rota = None
    menor_diferenca = float('inf')

    # Acha qual rota colocar o vértice
    for r_idx, rota in enumerate(solucao_candidata):
        capacidade = sum([problema.demands[cliente] for cliente in rota])
        nova_capacidade = capacidade + problema.demands[removido]

        # Checa se a rota ainda é viável
        if nova_capacidade > problema.capacity and precisa_ser_viavel:
            # Não vamos modificar essa rota
            continue

        # Acha a melhor posição de inserção nessa rota
        menor_diferenca_rota = float('inf')
        anterior = problema.depots[0]
        for idx, vertice in enumerate(rota):
            # Olha sempre o vértice atual e o anterior
            if (idx == 0): continue
            # Não por o vértice removido na posição original dele
            if (rota_removido == rota and idx_removido == idx): continue

            diferenca_atual = dist[anterior][removido] + dist[removido][vertice] - dist[anterior][vertice]

            if diferenca_atual < menor_diferenca_rota:
                melhor_posicao_rota = idx
                menor_diferenca_rota = diferenca_atual

            anterior = vertice

        # Checa se é a melhor rota pra adicionar o vértice
        if menor_diferenca_rota < menor_diferenca:
            melhor_rota = r_idx
            menor_diferenca = menor_diferenca_rota
            melhor_posicao = melhor_posicao_rota

    if melhor_rota is None:
        solucao_candidata.append([problema.depots[0], removido, problema.depots[0]])
    else:
        solucao_candidata[melhor_rota].insert(melhor_posicao, removido)

def viabilizacao (solucao_candidata, problema, dist):
    removidos = set() # Melhor para tirar e colocar elementos
    
    for rota in solucao_candidata:
        capacidade = sum([problema.demands[cliente] for cliente in rota])

        if capacidade <= problema.capacity:
            continue
        
        # Ordem crescente pelas demandas
        clientes_ordenados = sorted(rota[1:-1], key=lambda x: problema.demands[x])

        while capacidade > problema.capacity:
            # list.pop() é O(1) porque estamos tirando o último elemento da lista! :D
            cliente = clientes_ordenados.pop()
            capacidade -= problema.demands[cliente]
            removidos.add(cliente)
            rota.remove(cliente)

    for vertice in removidos:
        reinsercao_vertice(solucao_candidata, vertice, problema, dist, precisa_ser_viavel=True)

    return solucao_candidata

# Essa função usa pop() - e caso acabar os elementos da lista atual, vai para outra.
def remocao_vertice(solucao_candidata, rota=None, idx_remocao=None):

    if not solucao_candidata: return # Já retiramos todos os clientes da solução... talvez a perturbação esteja um pouco extrema

    # Checa se precisa pegar outra rota. (Nota: Às vezes a lista encurtou até idx_remocao ser o índice do depot)
    if (rota is None or len(rota) < 3 or idx_remocao == len(rota)-1): 
        # rota só com depot (2 vértices)
        if rota is not None and len(rota) < 3: 
            solucao_candidata.remove(rota)

        rota = random.choice(solucao_candidata)
        while len(rota) < 3: 
            rota = random.choice(solucao_candidata)

        # Não inclui depot no sorteio
        idx_remocao = random.choice(range(1, len(rota)-1))

    return rota, idx_remocao, rota.pop(idx_remocao)
    
def perturbacao (solucao_referencia, tamanho_perturbacao, problema, dist):
    # Isso precisa ser feito, para melhor_solucao e solucao_referencia não serem acidentalmente alteradas.
    solucao_candidata = copy.deepcopy(solucao_referencia)

    # TODO: Se tiver mais de uma heurística de remoção de vértices, sortear aqui.

    rota = None
    idx_remocao = None

    for _ in range(tamanho_perturbacao):
        rota, idx_remocao, removido = remocao_vertice(solucao_candidata, rota, idx_remocao)
        reinsercao_vertice(solucao_candidata, removido, problema, dist, rota, idx_remocao)

    return viabilizacao(solucao_candidata)

def AILS_II(problema, maximo_segundos, tamanho_perturbacao, quantidade_vizinhos):
    tempo_inicial = time.time()
    
    dist, vizinhos = calcula_matrizes(problema, quantidade_vizinhos)

    solucao_f1 = gera_solucao_inicial(problema, dist)

    solucao_f1 = busca_local(solucao_f1, problema, dist, vizinhos)
    
    melhor_solucao = copy.deepcopy(solucao_f1)
    melhor_custo = custo(melhor_solucao, dist)

    grupo_elite = []
    iteracoes_sem_melhora = 0
    fase = 1


    while time.time() - tempo_inicial < maximo_segundos:

        # Escolhe a fase
        # Se puder ir para a fase 2, a chance é 50%
        if (iteracoes_sem_melhora > 2000 and grupo_elite) and (random.choice([0, 1])):
            fase = 2
            solucao_referencia = random.choice(grupo_elite)
        else:
            fase = 1
            solucao_referencia = solucao_f1

        solucao_candidata = perturbacao(solucao_referencia, tamanho_perturbacao)
        solucao_candidata = busca_local(solucao_candidata, problema, dist, vizinhos)

        custo_candidata = custo(solucao_candidata, dist)

        if custo_candidata < melhor_custo:
            melhor_solucao = solucao_candidata
            melhor_custo = custo(melhor_solucao)
        else:
            iteracoes_sem_melhora += 1

        # (Grau de perturbação é constante, não precisa ser atualizado)

        if (fase == 1):
            # O critério de aceitação na fase 1 é Best (melhor para execuções curtas)
            if custo_candidata <= custo(solucao_referencia):
                solucao_f1 = solucao_candidata
        
        # (O critério de aceitação Best não pode ser atualizado)

def atualiza(rota, lista_movimentos, solucao_referencia, dist, vizinhos, problema):
    for idx, vertice in enumerate(rota):
        for vizinho in vizinhos[vertice]:
            # Queremos movimentos inter-rota aqui
            if vizinho in rota: continue
            if vizinho == problema.depots[0]: continue

            # Shift
            if (problema.demands[])






def busca_local(solucao_referencia, problema, dist, vizinhos):
    lista_movimentos = []

    for rota in solucao_referencia:
        atualiza(rota, lista_movimentos, solucao_referencia, dist, vizinhos, problema)

def main():
    arquivo = "instancias/A/A-n32-k5.vrp"
    problema = tsplib95.load(arquivo)

    melhor_solucao, melhor_custo = AILS_II(problema, maximo_segundos=300, tamanho_perturbacao=3, quantidade_vizinhos=5)


    
main()

# Testar a matriz distância
# test = [ [ str(int(e)).zfill(3) for e in l] for l in matriz_distancia]

# with open("out.txt", "w") as f:
#     print(test, file=f)
