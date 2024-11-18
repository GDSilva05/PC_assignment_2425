import sys
from croblink import *
from math import *
import xml.etree.ElementTree as ET
import time

CELLROWS = 7
CELLCOLS = 14
CELL_SIZE = 2    # Dimensione del lato della cella
ROBOT_DIAM = 1.0 # Diametro del robot
NOISE = 0.0      # Nessun rumore nei motori

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

# Funzione per verificare se tutte le direzioni in una cella sono aperte (senza muri)
def all_directions_open(i, j, cells):
    return not any(cells[i][j].values())

def compute_expected_measures(cells):
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

            # Caso 3: Spazio con muri adiacenti
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

            # Caso 5: Spazi aperti con condizioni specifiche (modificato)
            if D[0] is None and not wall_right and j + 1 < 14 and all_directions_open(i, j + 1, cells):
                if (j + 2 < 14 and i + 1 < 7 and cells[i + 1][j + 2]['left']) or \
                   (j + 2 < 14 and i - 1 >= 0 and cells[i - 1][j + 2]['left']):
                    D[0] = 2.6

            if D[1] is None and not wall_top and i + 1 < 7 and all_directions_open(i + 1, j, cells):
                if (i + 2 < 7 and j + 1 < 14 and cells[i + 2][j + 1]['bottom']) or \
                   (i + 2 < 7 and j - 1 >= 0 and cells[i + 2][j - 1]['bottom']):
                    D[1] = 2.6

            if D[2] is None and not wall_bottom and i - 1 >= 0 and all_directions_open(i - 1, j, cells):
                if (i - 2 >= 0 and j + 1 < 14 and cells[i - 2][j + 1]['top']) or \
                   (i - 2 >= 0 and j - 1 >= 0 and cells[i - 2][j - 1]['top']):
                    D[2] = 2.6

            if D[3] is None and not wall_left and j - 1 >= 0 and all_directions_open(i, j - 1, cells):
                if (j - 2 >= 0 and i + 1 < 7 and cells[i + 1][j - 2]['right']) or \
                   (j - 2 >= 0 and i - 1 >= 0 and cells[i - 1][j - 2]['right']):
                    D[3] = 2.6

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

            # Caso 8: Spazi aperti e muri in celle adiacenti (modificato)
            if D[0] is None and not wall_right and j + 1 < 14 and all_directions_open(i, j + 1, cells):
                if (j + 2 < 14 and cells[i][j + 2]['top'] and i + 1 < 7 and not cells[i + 1][j + 2]['left']) or \
                   (j + 2 < 14 and cells[i][j + 2]['bottom'] and i - 1 >= 0 and not cells[i - 1][j + 2]['left']):
                    D[0] = 2.66
            if D[1] is None and not wall_top and i + 1 < 7 and all_directions_open(i + 1, j, cells):
                if (i + 2 < 7 and cells[i + 2][j]['left'] and j - 1 >= 0 and not cells[i + 2][j - 1]['bottom']) or \
                   (i + 2 < 7 and cells[i + 2][j]['right'] and j + 1 < 14 and not cells[i + 2][j + 1]['bottom']):
                    D[1] = 2.66
            if D[2] is None and not wall_bottom and i - 1 >= 0 and all_directions_open(i - 1, j, cells):
                if (i - 2 >= 0 and cells[i - 2][j]['right'] and j + 1 < 14 and not cells[i - 2][j + 1]['top']) or \
                   (i - 2 >= 0 and cells[i - 2][j]['left'] and j - 1 >= 0 and not cells[i - 2][j - 1]['top']):
                    D[2] = 2.66
            if D[3] is None and not wall_left and j - 1 >= 0 and all_directions_open(i, j - 1, cells):
                if (j - 2 >= 0 and cells[i][j - 2]['top'] and i + 1 < 7 and not cells[i + 1][j - 2]['right']) or \
                   (j - 2 >= 0 and cells[i][j - 2]['bottom'] and i - 1 >= 0 and not cells[i - 1][j - 2]['right']):
                    D[3] = 2.66

            # Se D è ancora None, imposta a 3.0 (valore predefinito)
            for k in range(4):
                if D[k] is None:
                    D[k] = 3.0

            # Salva i valori di D per la cella corrente
            D_values[(i, j)] = D

    import math

    # Imposta il valore di noise
    noise = 0.1

    # Calcola i valori di M per ciascuna cella
    M_values = {}
    for key in D_values:
        D = D_values[key]
        M = []
        for d in D:
            # Calcola M, tronca alla prima cifra decimale
            m_value = 1 / d + noise
            truncated_m = math.trunc(m_value * 10) / 10
            M.append(truncated_m)
        M_values[key] = M

    return M_values

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
        for i in range(CELLROWS):
            for j in range(CELLCOLS):
                updated_probs[i][j] /= total_prob

        self.prob_map = updated_probs

        with open("localization.out", "a") as f:
            for row in reversed(self.prob_map):
                line = " ".join(f"{p:.4f}" for p in row)
                print(line)
                f.write(line + "\n")
            f.write("\n")

    def applyMovementModel(self, in_left_t, in_right_t):
        # Aggiorna `out_left` e `out_right` con la media dei valori attuali e precedenti
        self.out_left = (in_left_t + self.out_left) / 2
        self.out_right = (in_right_t + self.out_right) / 2

        # Calcola il movimento lineare del robot
        lin = (self.out_right + self.out_left) / 2
        self.distance_sum += lin  # Incrementa la distanza totale percorsa

        # Verifica se il robot ha completato un movimento di 2 unità (multiplo di 2)
        if self.distance_sum >= 2.0:
            print(f"Centro della cella raggiunto con distanza accumulata di {self.distance_sum} unità")
            self.updateLocalization()  # Aggiorna e stampa la tabella delle probabilità
            self.distance_sum -= 2.0  # Sottrae 2 per riavviare il conteggio per la prossima cella di 2 unità

    def run(self):
        if self.status != 0:
            print("Connessione rifiutata o errore")
            quit()

        stopped_state = 'run'
        print("Robot avviato")

        # Leggi i sensori una volta per inizializzare `measures` prima di usare `updateLocalization`
        self.readSensors()

        # **NUOVA CHIAMATA PER CONSIDERARE IL PUNTO INIZIALE COME CENTRO DELLA CELLA**
        self.updateLocalization()  # Inizializza la localizzazione dal punto di partenza

        while True:
            self.readSensors()

            if self.measures.endLed:
                print(self.rob_name + " exiting")
                quit()

            if self.state == 'stop' and self.measures.start:
                self.state = stopped_state

            if self.state != 'stop' and self.measures.stop:
                stopped_state = self.state
                self.state = 'stop'

            if self.state == 'run':
                if self.measures.visitingLed:
                    self.state = 'wait'
                if self.measures.ground == 0:
                    self.setVisitingLed(True)
                self.wander()
            elif self.state == 'wait':
                self.setReturningLed(True)
                if self.measures.visitingLed:
                    self.setVisitingLed(False)
                if self.measures.returningLed:
                    self.state = 'return'
                self.driveMotors(0.0, 0.0)
            elif self.state == 'return':
                if self.measures.visitingLed:
                    self.setVisitingLed(False)
                if self.measures.returningLed:
                    self.setReturningLed(False)
                self.wander()

    def wander(self):
        center_id = 0
        left_id = 1
        right_id = 2
        FRONT_THRESHOLD = 3.0

        if self.state == 'run':
            if self.measures.irSensor[center_id] > FRONT_THRESHOLD:
                if self.measures.irSensor[left_id] < self.measures.irSensor[right_id]:
                    print('Ostacolo davanti, fermo e ruota a sinistra')
                    self.state = 'rotate_left'
                else:
                    print('Ostacolo davanti, fermo e ruota a destra')
                    self.state = 'rotate_right'
            else:
                print('Percorso libero, vai avanti')
                # Passa i valori di input per il movimento in avanti
                self.applyMovementModel(0.1, 0.1)
                self.driveMotors(0.1, 0.1)

        elif self.state == 'rotate_left':
            self.applyMovementModel(-0.1, +0.1)
            time.sleep(1.5)
            self.driveMotors(0.0, 0.0)
            self.state = 'run'

        elif self.state == 'rotate_right':
            self.applyMovementModel(+0.1, -0.1)
            time.sleep(1.5)
            self.driveMotors(0.0, 0.0)
            self.state = 'run'

class Map():
    def __init__(self, filename):
        tree = ET.parse(filename)
        root = tree.getroot()

        self.labMap = [[' '] * (CELLCOLS*2-1) for i in range(CELLROWS*2-1)]
        for child in root.iter('Row'):
            line = child.attrib['Pattern']
            row = int(child.attrib['Pos'])
            if row % 2 == 0:
                for c in range(len(line)):
                    if (c+1) % 3 == 0:
                        if line[c] == '|':
                            self.labMap[row][(c+1)//3*2-1] = '|'
            else:
                for c in range(len(line)):
                    if c % 3 == 0:
                        if line[c] == '-':
                            self.labMap[row][c//3*2] = '-'

if __name__ == '__main__':
    rob_name = "pClient1"
    host = "localhost"
    pos = 1
    mapc = None

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

    cells = build_cells(labMap)
    M_values = compute_expected_measures(cells)

    rob = MyRob(rob_name, pos, [0.0, 90.0, -90.0, 180.0], host, M_values)
    rob.setMap(labMap)
    rob.printMap()

    rob.run()
