# Construir labMap a partir dos padrões fornecidos
patterns = [
    [' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', '·', '-', '-', '·', ' ', ' ', '·', '-', '-', '·', '-', '-', '·', ' ', ' ', '·', ' ', ' ', '·', '-', '-', '·', '-', '-', '·', '-', '-', '·', '-', '-', '·', ' ', ' ', '·', '-', '-', '·', '-', '-'],
    [' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' '],
    ['-', '-', '·', '-', '-', '·', ' ', ' ', '·', '-', '-', '·', ' ', ' ', '·', '-', '-', '·', '-', '-', '·', '-', '-', '·', ' ', ' ', '·', '-', '-', '·', '-', '-', '·', ' ', ' ', '·', '-', '-', '·', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', '|', ' ', ' '],
    ['-', '-', '·', '-', '-', '·', '-', '-', '·', ' ', ' ', '·', '-', '-', '·', ' ', ' ', '·', '-', '-', '·', '-', '-', '·', '-', '-', '·', ' ', ' ', '·', ' ', ' ', '·', ' ', ' ', '·', '-', '-', '·', ' ', ' '],
    [' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', '·', '-', '-', '·', '-', '-', '·', '-', '-', '·', '-', '-', '·', '-', '-', '·', '-', '-', '·', ' ', ' ', '·', ' ', ' ', '·', '-', '-', '·', ' ', ' ', '·', '-', '-', '·', '-', '-', '·', '-', '-'],
    [' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', '·', '-', '-', '·', ' ', ' ', '·', '-', '-', '·', '-', '-', '·', '-', '-', '·', '-', '-', '·', ' ', ' ', '·', '-', '-', '·', ' ', ' ', '·', ' ', ' ', '·', '-', '-', '·', ' ', ' ', '·', ' ', ' '],
    [' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' '],
    [' ', ' ', '·', '-', '-', '·', ' ', ' ', '·', '-', '-', '·', '-', '-', '·', '-', '-', '·', ' ', ' ', '·', '-', '-', '·', '-', '-', '·', ' ', ' ', '·', '-', '-', '·', ' ', ' ', '·', '-', '-', '·', ' ', ' '],
    [' ', ' ', '|', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' ', '|', ' ', ' ', ' ', ' ', ' ']
]

# Inverter a lista para alinhar o índice das células (linha 0 na parte inferior)
patterns = patterns[::-1]

# Construir labMap com comprimentos de linha consistentes
labMap = []
for pattern in patterns:
    labMap.append(pattern)

# Função para criar uma grade de células com informações sobre as paredes
def build_cells(labMap):
    cells = [[{'top': False, 'bottom': False, 'left': False, 'right': False} for j in range(14)] for i in range(7)]
    for i in range(7):  # i de 0 a 6
        for j in range(14):  # j de 0 a 13
            # Parede à direita
            if j <= 12:
                c = labMap[2 * i][3 * j + 2]
                cells[i][j]['right'] = c != ' '
            else:
                cells[i][j]['right'] = True  # Borda do mapa, considerada como parede

            # Parede à esquerda
            if j >= 1:
                c = labMap[2 * i][3 * j - 1]
                cells[i][j]['left'] = c != ' '
            else:
                cells[i][j]['left'] = True  # Borda do mapa, considerada como parede

            # Parede acima
            if i <= 5:
                wall_found = False
                for k in range(3 * j, 3 * j + 2):  # Intervalo alterado
                    if labMap[2 * i + 1][k] != ' ':
                        wall_found = True
                        break
                cells[i][j]['top'] = wall_found
            else:
                cells[i][j]['top'] = True  # Borda do mapa, considerada como parede

            # Parede abaixo
            if i >= 1:
                wall_found = False
                for k in range(3 * j, 3 * j + 2):  # Intervalo alterado
                    if labMap[2 * i - 1][k] != ' ':
                        wall_found = True
                        break
                cells[i][j]['bottom'] = wall_found
            else:
                cells[i][j]['bottom'] = True  # Borda do mapa, considerada como parede
    return cells

cells = build_cells(labMap)

# Função para verificar se todas as direções em uma célula estão abertas (sem paredes)
def all_directions_open(i, j):
    return not any(cells[i][j].values())

# Inicializar D_values
D_values = {}

# Loop principal para calcular os valores de D para cada célula e sensor
for i in range(7):
    for j in range(14):
        D = [None, None, None, None]  # D[0]: direita, D[1]: acima, D[2]: abaixo, D[3]: esquerda

        # Extrair informações sobre as paredes para a célula atual
        wall_right = cells[i][j]['right']
        wall_top = cells[i][j]['top']
        wall_bottom = cells[i][j]['bottom']
        wall_left = cells[i][j]['left']

        # Caso 1: Paredes imediatas
        if wall_right:
            D[0] = 0.4
        if wall_top:
            D[1] = 0.4
        if wall_bottom:
            D[2] = 0.4
        if wall_left:
            D[3] = 0.4

        # Caso 7: Sensores próximos às bordas com caminhos abertos
        if D[0] is None and not wall_right and j == 12 and j + 1 < 14:
            if not cells[i][j + 1]['top'] and not cells[i][j + 1]['bottom']:
                D[0] = 2.5
        if D[1] is None and not wall_top and (i == 5 or i == 4) and i + 1 < 7:
            if not cells[i + 1][j]['left'] and not cells[i + 1][j]['right']:
                D[1] = 2.5
        if D[2] is None and not wall_bottom and (i == 1 or i == 2) and i - 1 >= 0:
            if not cells[i - 1][j]['left'] and not cells[i - 1][j]['right']:
                D[2] = 2.5
        if D[3] is None and not wall_left and j == 1 and j - 1 >= 0:
            if not cells[i][j - 1]['top'] and not cells[i][j - 1]['bottom']:
                D[3] = 2.5

        # Caso 4: Bordas específicas e espaços adjacentes
        if D[0] is None and not wall_right:
            if (i == 0 and not cells[i][j + 1]['top']):
                D[0] = 2
            elif (i == 6 and not cells[i][j + 1]['bottom']):
                D[0] = 2
        if D[1] is None and not wall_top:
            if (j == 0 and not cells[i + 1][j]['right']):
                D[1] = 2
            elif (j == 13 and not cells[i + 1][j]['left']):
                D[1] = 2
        if D[2] is None and not wall_bottom:
            if (j == 0 and not cells[i - 1][j]['right']):
                D[2] = 2
            elif (j == 13 and not cells[i - 1][j]['left']):
                D[2] = 2
        if D[3] is None and not wall_left:
            if (i == 0 and not cells[i][j - 1]['top']):
                D[3] = 2
            elif (i == 6 and not cells[i][j - 1]['bottom']):
                D[3] = 2

        # Caso 3: Espaço com paredes adjacentes
        if D[0] is None and not wall_right and j + 1 < 14:
            if cells[i][j + 1]['top'] or cells[i][j + 1]['bottom']:
                D[0] = 1.8
        if D[1] is None and not wall_top and i + 1 < 7:
            if cells[i + 1][j]['left'] or cells[i + 1][j]['right']:
                D[1] = 1.8
        if D[2] is None and not wall_bottom and i - 1 >= 0:
            if cells[i - 1][j]['left'] or cells[i - 1][j]['right']:
                D[2] = 1.8
        if D[3] is None and not wall_left and j - 1 >= 0:
            if cells[i][j - 1]['top'] or cells[i][j - 1]['bottom']:
                D[3] = 1.8

        # Caso 5: Espaços abertos com condições específicas
        if D[0] is None and not wall_right and j + 1 < 14 and all_directions_open(i, j + 1):
            if (j + 2 < 14 and not cells[i][j + 2]['top'] and i + 1 < 7 and not cells[i + 1][j + 2]['left']) or \
               (j + 2 < 14 and not cells[i][j + 2]['bottom'] and i - 1 >= 0 and not cells[i - 1][j + 2]['left']):
                D[0] = 2.6
        if D[1] is None and not wall_top and i + 1 < 7 and all_directions_open(i + 1, j):
            if (j - 1 >= 0 and not cells[i + 1][j - 1]['top']) or (j + 1 < 14 and not cells[i + 1][j + 1]['top']):
                D[1] = 2.6
        if D[2] is None and not wall_bottom and i - 1 >= 0 and all_directions_open(i - 1, j):
            if (j - 1 >= 0 and not cells[i - 1][j - 1]['top']) or (j + 1 < 14 and not cells[i - 1][j + 1]['top']):
                D[2] = 2.6
        if D[3] is None and not wall_left and j - 1 >= 0 and all_directions_open(i, j - 1):
            if (j - 2 >= 0 and not cells[i][j - 2]['top'] and i + 1 < 7 and not cells[i + 1][j - 2]['right']) or \
               (j - 2 >= 0 and not cells[i][j - 2]['bottom'] and i - 1 >= 0 and not cells[i - 1][j - 2]['right']):
                D[3] = 2.6

        # Caso 6: Condições de espaço específicas com parede à frente
        if D[0] is None and not wall_right and j + 1 < 14:
            if not cells[i][j + 1]['top'] and not cells[i][j + 1]['bottom'] and cells[i][j + 1]['right']:
                D[0] = 2.4
        if D[1] is None and not wall_top and i + 1 < 7:
            if not cells[i + 1][j]['left'] and not cells[i + 1][j]['right'] and cells[i + 1][j]['top']:
                D[1] = 2.4
        if D[2] is None and not wall_bottom and i - 1 >= 0:
            if not cells[i - 1][j]['left'] and not cells[i - 1][j]['right'] and cells[i - 1][j]['bottom']:
                D[2] = 2.4
        if D[3] is None and not wall_left and j - 1 >= 0:
            if not cells[i][j - 1]['top'] and not cells[i][j - 1]['bottom'] and cells[i][j - 1]['left']:
                D[3] = 2.4

        # Caso 8: Espaços abertos e paredes em células adjacentes
        if D[0] is None and not wall_right and j + 1 < 14 and all_directions_open(i, j + 1):
            if (j + 2 < 14 and not cells[i][j + 2]['top'] and i + 1 < 7 and cells[i + 1][j + 2]['left']) or \
               (j + 2 < 14 and not cells[i][j + 2]['bottom'] and i - 1 >= 0 and cells[i - 1][j + 2]['left']):
                D[0] = 2.66
        if D[1] is None and not wall_top and i + 1 < 7 and all_directions_open(i + 1, j):
            if (i + 2 < 7 and not cells[i + 2][j]['left'] and j - 1 >= 0 and cells[i + 2][j - 1]['bottom']) or \
               (i + 2 < 7 and not cells[i + 2][j]['right'] and j + 1 < 14 and cells[i + 2][j + 1]['bottom']):
                D[1] = 2.66
        if D[2] is None and not wall_bottom and i - 1 >= 0 and all_directions_open(i - 1, j):
            if (i - 2 >= 0 and not cells[i - 2][j]['right'] and j + 1 < 14 and cells[i - 2][j + 1]['top']) or \
               (i - 2 >= 0 and not cells[i - 2][j]['left'] and j - 1 >= 0 and cells[i - 2][j - 1]['top']):
                D[2] = 2.66
        if D[3] is None and not wall_left and j - 1 >= 0 and all_directions_open(i, j - 1):
            if (j - 2 >= 0 and not cells[i][j - 2]['top'] and i + 1 < 7 and cells[i + 1][j - 2]['right']) or \
               (j - 2 >= 0 and not cells[i][j - 2]['bottom'] and i - 1 >= 0 and cells[i - 1][j - 2]['right']):
                D[3] = 2.66

        # Caso 2: Paredes nas bordas (avaliado por último)
        if i == 0:
            D[2] = 0.5  # Sensor 2 na linha 0
        if i == 6:
            D[1] = 0.5  # Sensor 1 na linha 6
        if j == 0:
            D[3] = 0.5  # Sensor 3 na coluna 0
        if j == 13:
            D[0] = 0.5  # Sensor 0 na coluna 13

        # Se D ainda é None, define como 3.0 (valor padrão)
        for k in range(4):
            if D[k] is None:
                D[k] = 3.0

        # Salva os valores de D para a célula atual
        D_values[(i, j)] = D

# Imprime os valores de D para cada célula
for key in sorted(D_values.keys()):
    print(f'Célula {key}: D0={D_values[key][0]}, D1={D_values[key][1]}, D2={D_values[key][2]}, D3={D_values[key][3]}')
