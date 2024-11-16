# Costruisci labMap dai pattern forniti
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

# Inverti la lista per allineare l'indice delle celle (riga 0 in basso)
patterns = patterns[::-1]

# Costruisci labMap con lunghezze di riga coerenti
labMap = []
for pattern in patterns:
    labMap.append(pattern)

# Funzione per creare una griglia di celle con informazioni sui muri
def build_cells(labMap):
    cells = [[{'top': False, 'bottom': False, 'left': False, 'right': False} for j in range(14)] for i in range(7)]
    for i in range(7):  # i da 0 a 6
        for j in range(14):  # j da 0 a 13
            # Muro a destra
            if j <= 12:
                c = labMap[2 * i][3 * j + 2]
                cells[i][j]['right'] = c != ' '
            else:
                cells[i][j]['right'] = True  # Bordo della mappa, considerato come muro

            # Muro a sinistra
            if j >= 1:
                c = labMap[2 * i][3 * j - 1]
                cells[i][j]['left'] = c != ' '
            else:
                cells[i][j]['left'] = True  # Bordo della mappa, considerato come muro

            # Muro in alto
            if i <= 5:
                wall_found = False
                for k in range(3 * j, 3 * j + 2):  # Cambiato intervallo
                    if labMap[2 * i + 1][k] != ' ':
                        wall_found = True
                        break
                cells[i][j]['top'] = wall_found
            else:
                cells[i][j]['top'] = True  # Bordo della mappa, considerato come muro

            # Muro in basso
            if i >= 1:
                wall_found = False
                for k in range(3 * j, 3 * j + 2):  # Cambiato intervallo
                    if labMap[2 * i - 1][k] != ' ':
                        wall_found = True
                        break
                cells[i][j]['bottom'] = wall_found
            else:
                cells[i][j]['bottom'] = True  # Bordo della mappa, considerato come muro
    return cells

cells = build_cells(labMap)

# Funzione per verificare se tutte le direzioni in una cella sono aperte (senza muri)
def all_directions_open(i, j):
    return not any(cells[i][j].values())

# Inizializza D_values
D_values = {}

# Ciclo principale per calcolare i valori di D per ogni cella e sensore
for i in range(7):
    for j in range(14):
        D = [None, None, None, None]  # D[0]: destra, D[1]: sopra, D[2]: sotto, D[3]: sinistra

        # Estrai le informazioni sui muri per la cella corrente
        wall_right = cells[i][j]['right']
        wall_top = cells[i][j]['top']
        wall_bottom = cells[i][j]['bottom']
        wall_left = cells[i][j]['left']

        # Caso 1: Muri immediati
        if wall_right:
            D[0] = 0.4
        if wall_top:
            D[1] = 0.4
        if wall_bottom:
            D[2] = 0.4
        if wall_left:
            D[3] = 0.4

        # Caso 2: Muri ai bordi
        if j == 13:
            D[0] = 0.5
        if i == 6:
            D[1] = 0.5
        if i == 0:
            D[2] = 0.5
        if j == 0:
            D[3] = 0.5

        # Caso 3: Spazio a destra/sopra/sotto/sinistra con muri adiacenti
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

        # Caso 4: Specifici bordi e spazi adiacenti
        if D[0] is None and not wall_right:
            if (i == 0 and j + 1 < 14 and not cells[i][j + 1]['top']):
                D[0] = 2
            if (i == 6 and j + 1 < 14 and not cells[i][j + 1]['bottom']):
                D[0] = 2
        if D[1] is None and not wall_top:
            if (j == 0 and i + 1 < 7 and not cells[i + 1][j]['right']):
                D[1] = 2
            if (j == 13 and i + 1 < 7 and not cells[i + 1][j]['left']):
                D[1] = 2
        if D[2] is None and not wall_bottom:
            if (j == 0 and i - 1 >= 0 and not cells[i - 1][j]['right']):
                D[2] = 2
            if (j == 13 and i - 1 >= 0 and not cells[i - 1][j]['left']):
                D[2] = 2
        if D[3] is None and not wall_left:
            if (i == 0 and j - 1 >= 0 and not cells[i][j - 1]['top']):
                D[3] = 2
            if (i == 6 and j - 1 >= 0 and not cells[i][j - 1]['bottom']):
                D[3] = 2

        # Caso 5: Spazi aperti con condizioni specifiche
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

        # Caso 6: Condizioni di spazio specifiche con muro davanti
        if D[0] is None and not wall_right and j + 1 < 14:
            if cells[i][j + 1]['top'] == False and cells[i][j + 1]['bottom'] == False and cells[i][j + 1]['right']:
                D[0] = 2.4
        if D[1] is None and not wall_top and i + 1 < 7:
            if cells[i + 1][j]['left'] == False and cells[i + 1][j]['right'] == False and cells[i + 1][j]['top']:
                D[1] = 2.4
        if D[2] is None and not wall_bottom and i - 1 >= 0:
            if cells[i - 1][j]['left'] == False and cells[i - 1][j]['right'] == False and cells[i - 1][j]['bottom']:
                D[2] = 2.4
        if D[3] is None and not wall_left and j - 1 >= 0:
            if cells[i][j - 1]['top'] == False and cells[i][j - 1]['bottom'] == False and cells[i][j - 1]['left']:
                D[3] = 2.4

        # Caso 7: Sensori vicino ai bordi con percorsi aperti
        if D[0] is None and not wall_right and j == 12 and j + 1 < 14:
            if not cells[i][j + 1]['top'] and not cells[i][j + 1]['bottom']:
                D[0] = 2.5
        if D[1] is None and not wall_top and i == 5 and i + 1 < 7:
            if not cells[i + 1][j]['left'] and not cells[i + 1][j]['right']:
                D[1] = 2.5
        if D[2] is None and not wall_bottom and i == 1 and i - 1 >= 0:
            if not cells[i - 1][j]['left'] and not cells[i - 1][j]['right']:
                D[2] = 2.5
        if D[3] is None and not wall_left and j == 1 and j - 1 >= 0:
            if not cells[i][j - 1]['top'] and not cells[i][j - 1]['bottom']:
                D[3] = 2.5

        # Caso 8: Spazi aperti e muri in celle adiacenti
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

        # Se D è ancora None, imposta a 3.0 (valore predefinito)
        for k in range(4):
            if D[k] is None:
                D[k] = 3.0

        # Salva i valori di D per la cella corrente
        D_values[(i, j)] = D

# Stampa i valori di D per ogni cella (opzionale, per debug)
for key in sorted(D_values.keys()):
    print(f'Cell {key}: D0={D_values[key][0]}, D1={D_values[key][1]}, D2={D_values[key][2]}, D3={D_values[key][3]}')
