import copy
import random
import time
import tsplib95
import math
import bisect
# Para leitura de arquivos 
import glob # Que nome majestoso
import os

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

            if len(vizinhos) < quantidade_vizinhos or d < distancias[i][vizinhos[-1]]:
                bisect.insort(vizinhos, j, key=lambda x: distancias[i][x])

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

def demanda_r(rota, problema, soma=0):
    for vertice in rota:
        soma += problema.demands[vertice]

    return soma

def custo(solucao, dist):
    # Opção para criar soluções de custo infinito
    if solucao == [[float('inf')]]: 
        return float('inf')
    
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

    return viabilizacao(solucao_candidata, problema, dist)

def ILS(problema, maximo_segundos, tamanho_perturbacao, quantidade_vizinhos):
    tempo_inicial = time.time()
    
    dist, vizinhos = calcula_matrizes(problema, quantidade_vizinhos)

    solucao_referencia = gera_solucao_inicial(problema, dist)
    solucao_referencia = busca_local(solucao_referencia, problema, dist, vizinhos)
    
    melhor_solucao = copy.deepcopy(solucao_referencia)
    melhor_custo = custo(melhor_solucao, dist)

    while time.time() - tempo_inicial < maximo_segundos:
        solucao_candidata = perturbacao(solucao_referencia, tamanho_perturbacao, problema, dist)
        solucao_candidata = busca_local(solucao_candidata, problema, dist, vizinhos)

        custo_candidata = custo(solucao_candidata, dist)

        if custo_candidata < melhor_custo:
            melhor_solucao = solucao_candidata
            melhor_custo = custo(melhor_solucao, dist)

        # (Grau de perturbação é constante, não precisa ser atualizado)
    
        # O critério de aceitação é Best (melhor para execuções curtas)
        if custo_candidata <= custo(solucao_referencia, dist):
            solucao_referencia = solucao_candidata
        
        # (O critério de aceitação Best não pode ser atualizado)
    
    return melhor_solucao, melhor_custo

# Assume que rota e solucao_referencia são válidas
def atualiza(rota, lista_solucoes, solucao_referencia, dist, vizinhos, problema):
    # Gera o melhor movimento entre cada par de vértice
    for vertice in rota:
        if vertice == problema.depots[0]: continue
        for vizinho in vizinhos[vertice]:
            if vizinho == problema.depots[0]: continue

            if vizinho in rota:
                rota_vizinho = rota
            else:
                rota_vizinho = next((r for r in solucao_referencia if vizinho in r))

            resto_da_solucao = [r for r in solucao_referencia if r != rota and r != rota_vizinho]
            
            # Para não ter que ficar calculando nos ifs
            demanda_rota = demanda_r(rota, problema)
            demanda_rota_vizinho = demanda_r(rota_vizinho, problema)
            # Para deixar mais legível
            demanda_vizinho = problema.demands[vizinho]
            demanda_vertice = problema.demands[vertice]

            # Para caso crie solução inválida, ele não seja escolhido
            shift = [[float('inf')]]
            swap = [[float('inf')]]
            dois_opt = [[float('inf')]]

            # Shift
            if (demanda_rota + demanda_vizinho <= problema.capacity):
                # Adiciona o vizinho a nossa rota
                rota_maior = list(rota)
                rota_maior.insert(-1,vizinho)

                # Remove o vizinho da rota dele
                rota_menor = list(rota_vizinho)
                rota_menor.remove(vizinho)

                shift = [rota_maior] + [rota_menor] + resto_da_solucao

            # Swap
            # "Trocar eu com o meu vizinho não passa a minha rota do limite, nem a dele"
            if (demanda_rota - demanda_vertice + demanda_vizinho <= problema.capacity and 
                    demanda_rota_vizinho - demanda_vizinho + demanda_vertice <= problema.capacity):
                
                rotas_com_elementos_trocados = [[c if c != vertice else vizinho for c in rota]] + [[c if c != vizinho else vertice for c in rota_vizinho]]
                
                swap = rotas_com_elementos_trocados + resto_da_solucao

            # O famoso 2-opt: trocando seções inteiras das rotas!
            corte = random.choice( range(1, min( len(rota), len(rota_vizinho) )-1) )

            rota_comeco = rota[:corte] + rota_vizinho[corte:]
            rota_vizinho_comeco = rota_vizinho[:corte] + rota[corte:]
            
            if (demanda_r(rota_comeco, problema) <= problema.capacity and 
                    demanda_r(rota_vizinho_comeco, problema) <= problema.capacity):
                dois_opt = [rota_comeco] + [rota_vizinho_comeco] + resto_da_solucao

            # Avalia qual o melhor
            melhor_solucao = min(shift, swap, dois_opt, key= lambda x: custo(x, dist))

            # Se essa mudança de dois vértices melhorou a solução, podemos considerar ela.
            if (custo(melhor_solucao, dist) < custo(solucao_referencia, dist)):
                lista_solucoes.append(melhor_solucao)

def busca_local(solucao_referencia, problema, dist, vizinhos):
    lista_solucoes = []

    for rota in solucao_referencia:
        # Testa movimentos em cada par de vértice, retorna soluções melhores que solucao_referencia
        atualiza(rota, lista_solucoes, solucao_referencia, dist, vizinhos, problema)

    return min(lista_solucoes, key=lambda x: custo(x, dist)) if lista_solucoes else solucao_referencia

def main():
    arquivos = glob.glob(os.path.join('instancias', 'TESTE', '*'))

    with open("resultados.txt", "w") as resultados:
        print(f"{'Instancia':<15}{'tp':<5}{'qv':<5}{'valor final'}", file=resultados)

        for arquivo in arquivos:
            for _ in range(5):

                problema = tsplib95.load(arquivo)

                melhor_solucao, melhor_custo = ILS(problema, maximo_segundos=1, tamanho_perturbacao=3, quantidade_vizinhos=10)

                print(f"{problema.name:<15}{tamanho_perturbacao:<5}{quantidade_vizinhos:<5}{melhor_custo}", file=resultados)
            # Para caso algo crashe, não perder toda informação
            resultados.flush()

main()