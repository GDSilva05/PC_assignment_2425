import sys
from croblink import *
from math import *
import xml.etree.ElementTree as ET
import time
import argparse

CELLROWS = 7
CELLCOLS = 14
CELL_SIZE = 2    # Dimensione del lato della cella
ROBOT_DIAM = 1.0 # Diametro del robot
NOISE = 0.0      # Nessun rumore nei motori

# Funzione para parsear o XML
def parse_lab_file(file_path):
    # Carrega o XML
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Encontra todas as linhas (Row)
    rows = root.findall("Row")
    max_width = int(root.get("Width"))
    
    # Ordena as linhas com base na posição (Pos) decrescente
    rows_sorted = sorted(rows, key=lambda x: int(x.get("Pos")), reverse=True)
    
    patterns = []
    
    for row in rows_sorted:
        pattern_str = row.get("Pattern")  # Lê o padrão da linha
        # Cria uma lista de caracteres a partir da string do padrão
        pattern_list = list(pattern_str.ljust(max_width, ' '))
        patterns.append(pattern_list)  # Adiciona a linha ao padrão
    
    return patterns

# Funzione per creare una griglia di celle con informazioni sui muri
def build_cells(labMap):
    cells = [[{'top': False, 'bottom': False, 'left': False, 'right': False} for j in range(CELLCOLS)] for i in range(CELLROWS)]
    for i in range(CELLROWS):  # i da 0 a CELLROWS-1
        for j in range(CELLCOLS):  # j da 0 a CELLCOLS-1
            # Muro a destra
            if j <= CELLCOLS - 2:
                c = labMap[2 * i][3 * j + 2]
                cells[i][j]['right'] = c != ' '
            else:
                cells[i][j]['right'] = True  # Bordo della mappa, considerato como muro

            # Muro a sinistra
            if j >= 1:
                c = labMap[2 * i][3 * j - 1]
                cells[i][j]['left'] = c != ' '
            else:
                cells[i][j]['left'] = True  # Bordo della mappa, considerato como muro

            # Muro in alto
            if i <= CELLROWS - 2:
                wall_found = False
                for k in range(3 * j, 3 * j + 2):  # Cambiato intervallo
                    if labMap[2 * i + 1][k] != ' ':
                        wall_found = True
                        break
                cells[i][j]['top'] = wall_found
            else:
                cells[i][j]['top'] = True  # Bordo della mappa, considerato como muro

            # Muro in basso
            if i >= 1:
                wall_found = False
                for k in range(3 * j, 3 * j + 2):  # Cambiato intervallo
                    if labMap[2 * i - 1][k] != ' ':
                        wall_found = True
                        break
                cells[i][j]['bottom'] = wall_found
            else:
                cells[i][j]['bottom'] = True  # Bordo della mappa, considerato como muro
    return cells

# Funzione per verificare se tutte le direzioni in una cella sono aperte (senza muri)
def all_directions_open(i, j, cells):
    return not any(cells[i][j].values())

def compute_expected_measures(cells):
    # Inizializza D_values
    D_values = {}

    # Ciclo principale per calcolare i valori di D per ogni cella e sensore
    for i in range(CELLROWS):
        for j in range(CELLCOLS):
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
            if j == CELLCOLS - 1:
                D[0] = 0.5
            if i == CELLROWS - 1:
                D[1] = 0.5
            if i == 0:
                D[2] = 0.5
            if j == 0:
                D[3] = 0.5

            # Caso 4: Specifici bordi e spazi adiacenti
            if D[0] is None and not wall_right:
                if (i == 0 and j + 1 < CELLCOLS and not cells[i][j + 1]['top']):
                    D[0] = 2
                if (i == CELLROWS - 1 and j + 1 < CELLCOLS and not cells[i][j + 1]['bottom']):
                    D[0] = 2
            if D[1] is None and not wall_top:
                if (j == 0 and i + 1 < CELLROWS and not cells[i + 1][j]['right']):
                    D[1] = 2
                if (j == CELLCOLS - 1 and i + 1 < CELLROWS and not cells[i + 1][j]['left']):
                    D[1] = 2
            if D[2] is None and not wall_bottom:
                if (j == 0 and i - 1 >= 0 and not cells[i - 1][j]['right']):
                    D[2] = 2
                if (j == CELLCOLS - 1 and i - 1 >= 0 and not cells[i - 1][j]['left']):
                    D[2] = 2
            if D[3] is None and not wall_left:
                if (i == 0 and j - 1 >= 0 and not cells[i][j - 1]['top']):
                    D[3] = 2
                if (i == CELLROWS - 1 and j - 1 >= 0 and not cells[i][j - 1]['bottom']):
                    D[3] = 2

            # Caso 3: Spazio con muri adiacenti
            if D[0] is None and not wall_right and j + 1 < CELLCOLS:
                if cells[i][j + 1]['top'] or cells[i][j + 1]['bottom']:
                    D[0] = 1.8
            if D[1] is None and not wall_top and i + 1 < CELLROWS:
                if cells[i + 1][j]['left'] or cells[i + 1][j]['right']:
                    D[1] = 1.8
            if D[2] is None and not wall_bottom and i - 1 >= 0:
                if cells[i - 1][j]['left'] or cells[i - 1][j]['right']:
                    D[2] = 1.8
            if D[3] is None and not wall_left and j - 1 >= 0:
                if cells[i][j - 1]['top'] or cells[i][j - 1]['bottom']:
                    D[3] = 1.8

            # Caso 5: Spazi aperti con condizioni specifiche (modificato)
            if D[0] is None and not wall_right and j + 1 < CELLCOLS and all_directions_open(i, j + 1, cells):
                if (j + 2 < CELLCOLS and i + 1 < CELLROWS and cells[i + 1][j + 2]['left']) or \
                   (j + 2 < CELLCOLS and i - 1 >= 0 and cells[i - 1][j + 2]['left']):
                    D[0] = 2.6

            if D[1] is None and not wall_top and i + 1 < CELLROWS and all_directions_open(i + 1, j, cells):
                if (i + 2 < CELLROWS and j + 1 < CELLCOLS and cells[i + 2][j + 1]['bottom']) or \
                   (i + 2 < CELLROWS and j - 1 >= 0 and cells[i + 2][j - 1]['bottom']):
                    D[1] = 2.6

            if D[2] is None and not wall_bottom and i - 1 >= 0 and all_directions_open(i - 1, j, cells):
                if (i - 2 >= 0 and j + 1 < CELLCOLS and cells[i - 2][j + 1]['top']) or \
                   (i - 2 >= 0 and j - 1 >= 0 and cells[i - 2][j - 1]['top']):
                    D[2] = 2.6

            if D[3] is None and not wall_left and j - 1 >= 0 and all_directions_open(i, j - 1, cells):
                if (j - 2 >= 0 and i + 1 < CELLROWS and cells[i + 1][j - 2]['right']) or \
                   (j - 2 >= 0 and i - 1 >= 0 and cells[i - 1][j - 2]['right']):
                    D[3] = 2.6

            # Caso 7: Sensori vicino ai bordi con percorsi aperti
            if D[0] is None and not wall_right and j == CELLCOLS - 2 and j + 1 < CELLCOLS:
                if not cells[i][j + 1]['top'] and not cells[i][j + 1]['bottom']:
                    D[0] = 2.5
            if D[1] is None and not wall_top and i == CELLROWS - 2 and i + 1 < CELLROWS:
                if not cells[i + 1][j]['left'] and not cells[i + 1][j]['right']:
                    D[1] = 2.5
            if D[2] is None and not wall_bottom and i == 1 and i - 1 >= 0:
                if not cells[i - 1][j]['left'] and not cells[i - 1][j]['right']:
                    D[2] = 2.5
            if D[3] is None and not wall_left and j == 1 and j - 1 >= 0:
                if not cells[i][j - 1]['top'] and not cells[i][j - 1]['bottom']:
                    D[3] = 2.5

            # Caso 6: Condizioni di spazio specifiche con muro davanti
            if D[0] is None and not wall_right and j + 1 < CELLCOLS:
                if not cells[i][j + 1]['top'] and not cells[i][j + 1]['bottom'] and cells[i][j + 1]['right']:
                    D[0] = 2.4
            if D[1] is None and not wall_top and i + 1 < CELLROWS:
                if not cells[i + 1][j]['left'] and not cells[i + 1][j]['right'] and cells[i + 1][j]['top']:
                    D[1] = 2.4
            if D[2] is None and not wall_bottom and i - 1 >= 0:
                if not cells[i - 1][j]['left'] and not cells[i - 1][j]['right'] and cells[i - 1][j]['bottom']:
                    D[2] = 2.4
            if D[3] is None and not wall_left and j - 1 >= 0:
                if not cells[i][j - 1]['top'] and not cells[i][j - 1]['bottom'] and cells[i][j - 1]['left']:
                    D[3] = 2.4

            # Caso 8: Spazi aperti e muri in celle adiacenti (modificato)
            if D[0] is None and not wall_right and j + 1 < CELLCOLS and all_directions_open(i, j + 1, cells):
                if (j + 2 < CELLCOLS and cells[i][j + 2]['top'] and i + 1 < CELLROWS and not cells[i + 1][j + 2]['left']) or \
                   (j + 2 < CELLCOLS and cells[i][j + 2]['bottom'] and i - 1 >= 0 and not cells[i - 1][j + 2]['left']):
                    D[0] = 2.66
            if D[1] is None and not wall_top and i + 1 < CELLROWS and all_directions_open(i + 1, j, cells):
                if (i + 2 < CELLROWS and cells[i + 2][j]['left'] and j - 1 >= 0 and not cells[i + 2][j - 1]['bottom']) or \
                   (i + 2 < CELLROWS and cells[i + 2][j]['right'] and j + 1 < CELLCOLS and not cells[i + 2][j + 1]['bottom']):
                    D[1] = 2.66
            if D[2] is None and not wall_bottom and i - 1 >= 0 and all_directions_open(i - 1, j, cells):
                if (i - 2 >= 0 and cells[i - 2][j]['right'] and j + 1 < CELLCOLS and not cells[i - 2][j + 1]['top']) or \
                   (i - 2 >= 0 and cells[i - 2][j]['left'] and j - 1 >= 0 and not cells[i - 2][j - 1]['top']):
                    D[2] = 2.66
            if D[3] is None and not wall_left and j - 1 >= 0 and all_directions_open(i, j - 1, cells):
                if (j - 2 >= 0 and cells[i][j - 2]['top'] and i + 1 < CELLROWS and not cells[i + 1][j - 2]['right']) or \
                   (j - 2 >= 0 and cells[i][j - 2]['bottom'] and i - 1 >= 0 and not cells[i - 1][j - 2]['right']):
                    D[3] = 2.66

            # Se D è ancora None, imposta a 3.0 (valore predefinito)
            for k in range(4):
                if D[k] is None:
                    D[k] = 3.0

            # Salva i valori di D per la cella corrente
            D_values[(i, j)] = D

    # Imposta il valore di noise
    noise = 0.1

    # Calcola i valori di M per ciascuna cella
    M_values = {}
    for key in D_values:
        D = D_values[key]
        M = []
        for d in D:
            # Calcola M, tronca alla primeira cifra decimale
            m_value = 1 / d + noise
            # truncated_m = math.trunc(m_value * 10) / 10
            rounded_m = round(m_value, 1)
            M.append(rounded_m)
            # M.append(truncated_m)
        M_values[key] = M

    return M_values

# Definição da classe MyRob (mantida conforme seu código original)
class MyRob(CRobLinkAngs):
    def __init__(self, rob_name, rob_id, angles, host, M_values):
        CRobLinkAngs.__init__(self, rob_name, rob_id, angles, host)
        self.prob_map = [[1.0 / (CELLROWS * CELLCOLS)] * CELLCOLS for _ in range(CELLROWS)]
        self.state = 'stop'
        self.distance_sum = 0.0  # Somma delle distanze percorse
        self.out_left = 0.0      # Potenza applicata al motore sinistro al tempo t-1 (inizialmente fermo)
        self.out_right = 0.0     # Potenza applicata al motore destro al tempo t-1 (inizialmente fermo)
        self.M_values = M_values
        self.noise = 0.1  # Standard deviation for sensor noise
        self.file_name = "localization.out"

        # Clear the file at the start
        with open(self.file_name, "w") as f:
            f.write("")

    def setMap(self, labMap):
        self.labMap = labMap

    def printMap(self):
        for l in reversed(self.labMap):
            print(''.join([str(l) for l in l]))

    def getExpectedMeasures(self, i, j):
        # Restituisce i valori di M per la cella (i, j)
        return self.M_values[(i, j)]

    def gaussian_prob(self, mu, sigma, x):
        return (1.0 / (sqrt(2 * pi) * sigma)) * exp(-0.5 * ((x - mu) ** 2) / (sigma ** 2))

    def motionUpdate(self, lin, ang):
        # Initialize a new probability map with zeros
        new_prob_map = [[0.0 for _ in range(CELLCOLS)] for _ in range(CELLROWS)]

        # Define motion uncertainty (you can adjust these values)
        motion_noise = 0  # Standard deviation for movement
        possible_moves = [(0, 1)]  # Forward

        for i in range(CELLROWS):
            for j in range(CELLCOLS):
                prob = self.prob_map[i][j]
                if prob > 0:
                    for move in possible_moves:
                        new_i = i + move[0]
                        new_j = j + move[1]
                        if 0 <= new_i < CELLROWS and 0 <= new_j < CELLCOLS:
                            # Distribute the probability to neighboring cells
                            new_prob_map[new_i][new_j] += prob * (1 - motion_noise) / len(possible_moves)
                        else:
                            # Probability of hitting a wall or boundary
                            new_prob_map[i][j] += prob * motion_noise / len(possible_moves)

        # Normalize the new probability map
        total_prob = sum(sum(row) for row in new_prob_map)
        for i in range(CELLROWS):
            for j in range(CELLCOLS):
                new_prob_map[i][j] /= total_prob

        self.prob_map = new_prob_map  # Update the probability map with motion update

        # Print the probability map after motion update
        print("Probability map after motion update:")
        self.printProbabilityMap()

    def updateLocalization(self):
        sensor_readings = [
            self.measures.irSensor[0],
            self.measures.irSensor[1],
            self.measures.irSensor[2],
            self.measures.irSensor[3]
        ]

        # Stampa i valori dei sensori al centro della cella
        print("Valori dei sensori al centro della cella:", sensor_readings)

        updated_probs = []
        for i in range(CELLROWS):
            row_probs = []
            for j in range(CELLCOLS):
                prior = self.prob_map[i][j]
                likelihood = 1.0
                expected_measures = self.getExpectedMeasures(i, j)

                for sensor_value, expected_value in zip(sensor_readings, expected_measures):
                    likelihood *= self.gaussian_prob(expected_value, self.noise, sensor_value)

                posterior = likelihood * prior
                row_probs.append(posterior)
            updated_probs.append(row_probs)

        total_prob = sum(sum(row) for row in updated_probs)
        if total_prob > 0:
            for i in range(CELLROWS):
                for j in range(CELLCOLS):
                    updated_probs[i][j] /= total_prob
        else:
            # Handle the case where total_prob is zero to avoid division by zero
            updated_probs = self.prob_map  # Keep the prior if measurement likelihood is zero

        self.prob_map = updated_probs

        # Print the probability map after measurement update
        print("Probability map after measurement update:")
        self.printProbabilityMap()

    def printProbabilityMap(self):
        for row in reversed(self.prob_map):
            line = " ".join(f"{p:.4f}" for p in row)
            print(line)
        print("\n")
        
        # Append to file
        with open(self.file_name, "a") as f:
            for row in reversed(self.prob_map):
                line = " ".join(f"{p:.4f}" for p in row)
                f.write(line + "\n")
            f.write("\n")  # Add a blank line to separate tables

    def applyMovementModel(self, in_left_t, in_right_t):
        # Update movement outputs
        self.out_left = in_left_t
        self.out_right = in_right_t

        # Calculate linear and angular movements
        lin = (self.out_right + self.out_left) / 2
        ang = (self.out_right - self.out_left) / ROBOT_DIAM

        # Update distance sum
        self.distance_sum += lin

        # If the robot has moved approximately one cell size, perform motion update
        if self.distance_sum >= CELL_SIZE:
            print(f"Moved one cell size with accumulated distance {self.distance_sum}")
            self.motionUpdate(lin, ang)  # Perform the motion update
            self.updateLocalization()    # Update and print the probability map after motion
            self.distance_sum -= CELL_SIZE  # Reset the distance sum for the next cell

    def run(self):
        if self.status != 0:
            print("Connessione rifiutata o errore")
            quit()

        print("Robot avviato")

        # Leggi i sensori una volta per inizializzare `measures` prima di usare `updateLocalization`
        self.readSensors()

        # Inizializza la localizzazione dal punto di partenza
        self.updateLocalization()

        while True:
            self.readSensors()

            if self.measures.endLed:
                print(self.rob_name + " exiting")
                quit()

            if self.state == 'stop' and self.measures.start:
                self.state = 'run'

            if self.state != 'stop' and self.measures.stop:
                self.state = 'stop'

            if self.state == 'run':
                # Remova ou comente as seguintes linhas
                # if self.measures.visitingLed:
                #     self.state = 'wait'
                # if self.measures.ground == 0:
                #     self.setVisitingLed(True)
                self.wander()
            # Remova o bloco elif para o estado 'wait' se não for mais necessário
            # elif self.state == 'wait':
            #     self.setReturningLed(True)
            #     if self.measures.visitingLed:
            #         self.setVisitingLed(False)
            #     if self.measures.returningLed:
            #         self.state = 'return'
            #     self.driveMotors(0.0, 0.0)
            elif self.state == 'return':
                if self.measures.visitingLed:
                    self.setVisitingLed(False)
                if self.measures.returningLed:
                    self.setReturningLed(False)
                self.wander()

    def wander(self):
        center_id = 0  # Índice do sensor frontal
        FRONT_THRESHOLD = 0.5  # Ajuste este valor conforme necessário

        if self.state == 'run':
            if self.measures.irSensor[0] > 2.6:  # Supondo que exista um atributo para colisão
                print('Colisão detectada, parando o robô.')
                self.driveMotors(0.0, 0.0)
                self.state = 'stop'
            else:
                print('Caminho livre, continuando em frente.')
                self.applyMovementModel(0.1, 0.1)
                self.driveMotors(0.1, 0.1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Localização e Controle do Robô.')
    parser.add_argument('--host', '-H', type=str, default='localhost', help='Endereço do host')
    parser.add_argument('--pos', '-p', type=int, default=1, help='Posição inicial do robô')
    parser.add_argument('--robname', '-r', type=str, default='pClient1', help='Nome do robô')
    parser.add_argument('--map', '-m', type=str, required=True, help='Caminho para o ficheiro XML do mapa')

    args = parser.parse_args()

    rob_name = args.robname
    host = args.host
    pos = args.pos
    xml_file_path = args.map

    # Ler os padrões do ficheiro XML
    try:
        patterns = parse_lab_file(xml_file_path)
    except Exception as e:
        print(f"Erro ao ler o ficheiro XML: {e}")
        quit()

    # Inverter a lista para alinhar o índice das células (linha 0 em baixo)
    patterns = patterns[::-1]

    # Construir labMap com comprimentos de linha coerentes
    labMap = []
    for pattern in patterns:
        labMap.append(pattern)

    # Construir as células e calcular os valores esperados
    cells = build_cells(labMap)
    M_values = compute_expected_measures(cells)

    # Inicializar o robô com o mapa lido
    rob = MyRob(rob_name, pos, [0.0, 90.0, -90.0, 180.0], host, M_values)
    rob.setMap(labMap)
    rob.printMap()

    # Executar o robô
    rob.run()