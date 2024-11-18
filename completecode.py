import sys
import math
from croblink import *
import time

CELLROWS = 7
CELLCOLS = 14
CELL_SIZE = 2    # Tamanho da célula
ROBOT_DIAM = 1.0 # Diâmetro do robô
NOISE = 1.0      # Desvio padrão para o ruído dos sensores (ajustado para 1.0)

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

class MyRob(CRobLinkAngs):
    def __init__(self, rob_name, rob_id, angles, host):
        CRobLinkAngs.__init__(self, rob_name, rob_id, angles, host)
        self.prob_map = [[1.0 / (CELLROWS * CELLCOLS)] * CELLCOLS for _ in range(CELLROWS)]
        self.state = 'stop'
        self.distance_sum = 0.0
        self.out_left = 0.0
        self.out_right = 0.0
        self.current_position = (0, 0)  # Acompanhar a posição estimada atual do robô

    def setMap(self, labMap):
        self.labMap = labMap
        self.cells = self.build_cells(self.labMap)
        self.D_values = self.compute_D_values(self.cells)
        self.M_values = self.compute_M_values(self.D_values)

    def build_cells(self, labMap):
        cells = [[{'top': False, 'bottom': False, 'left': False, 'right': False} for j in range(14)] for i in range(7)]
        for i in range(7):
            for j in range(14):
                # Parede à direita
                if j <= 12:
                    c = labMap[2 * i][3 * j + 2]
                    cells[i][j]['right'] = c != ' '
                else:
                    cells[i][j]['right'] = True

                # Parede à esquerda
                if j >= 1:
                    c = labMap[2 * i][3 * j - 1]
                    cells[i][j]['left'] = c != ' '
                else:
                    cells[i][j]['left'] = True

                # Parede acima
                if i <= 5:
                    wall_found = False
                    for k in range(3 * j, 3 * j + 2):
                        if labMap[2 * i + 1][k] != ' ':
                            wall_found = True
                            break
                    cells[i][j]['top'] = wall_found
                else:
                    cells[i][j]['top'] = True

                # Parede abaixo
                if i >= 1:
                    wall_found = False
                    for k in range(3 * j, 3 * j + 2):
                        if labMap[2 * i - 1][k] != ' ':
                            wall_found = True
                            break
                    cells[i][j]['bottom'] = wall_found
                else:
                    cells[i][j]['bottom'] = True
        return cells

    def all_directions_open(self, i, j):
        return not any(self.cells[i][j].values())

    def compute_D_values(self, cells):
        D_values = {}
        for i in range(7):
            for j in range(14):
                D = [None, None, None, None]  # D[0]: direita, D[1]: cima, D[2]: baixo, D[3]: esquerda

                # Extrair informações sobre as paredes
                wall_right = cells[i][j]['right']
                wall_top = cells[i][j]['top']
                wall_bottom = cells[i][j]['bottom']
                wall_left = cells[i][j]['left']

                # Atribuir distâncias com base nas paredes
                D[0] = 0.4 if wall_right else 3.0
                D[1] = 0.4 if wall_top else 3.0
                D[2] = 0.4 if wall_bottom else 3.0
                D[3] = 0.4 if wall_left else 3.0

                D_values[(i, j)] = D
        return D_values

    def compute_M_values(self, D_values):
        M_values = {}
        for key in D_values:
            D = D_values[key]
            M = []
            for d in D:
                m_value = 1 / d + NOISE
                m_value = round(m_value, 1)
                M.append(m_value)
            M_values[key] = M
        return M_values

    def getExpectedMeasures(self, i, j):
        M = self.M_values[(i, j)]
        # Reordenar M para corresponder à orientação dos sensores: [frente, esquerda, direita, trás]
        expected_measures = [M[0], M[1], M[2], M[3]]  # Ajuste para corresponder ao seu código de movimento
        return expected_measures

    def gaussian_prob(self, mu, sigma, x):
        return (1.0 / (math.sqrt(2 * math.pi) * sigma)) * math.exp(-0.5 * ((x - mu) ** 2) / (sigma ** 2))

    def updateLocalization(self):
        sensor_readings = [
            self.measures.irSensor[0],  # frente
            self.measures.irSensor[1],  # esquerda
            self.measures.irSensor[2],  # direita
            self.measures.irSensor[3]   # trás
        ]

        print("Leituras dos sensores:", sensor_readings)

        updated_probs = []
        for i in range(CELLROWS):
            row_probs = []
            for j in range(CELLCOLS):
                prior_prob = self.prob_map[i][j]
                expected_measures = self.getExpectedMeasures(i, j)
                prob = prior_prob
                for sensor_value, expected_value in zip(sensor_readings, expected_measures):
                    likelihood = self.gaussian_prob(expected_value, NOISE, sensor_value)
                    prob *= likelihood
                row_probs.append(prob)
            updated_probs.append(row_probs)

        total_prob = sum(sum(row) for row in updated_probs)
        if total_prob == 0:
            print("A probabilidade total é zero, não é possível normalizar")
            return
        for i in range(CELLROWS):
            for j in range(CELLCOLS):
                updated_probs[i][j] /= total_prob

        self.prob_map = updated_probs

        # Escrever as probabilidades em um arquivo e imprimir
        with open("localization.out", "a") as f:
            for row in reversed(self.prob_map):
                line = " ".join(f"{p:.4f}" for p in row)
                print(line)
                f.write(line + "\n")
            f.write("\n")

    def applyMotionModel(self, movement):
        # Passo de previsão do modelo de movimento
        new_prob_map = [[0.0 for _ in range(CELLCOLS)] for _ in range(CELLROWS)]
        p_correct = 0.8
        p_stay = 0.2

        for i in range(CELLROWS):
            for j in range(CELLCOLS):
                prob = self.prob_map[i][j]
                if prob > 0:
                    if movement == "forward" and i + 1 < CELLROWS:
                        new_prob_map[i + 1][j] += prob * p_correct
                        new_prob_map[i][j] += prob * p_stay
                    elif movement == "left" and j - 1 >= 0:
                        new_prob_map[i][j - 1] += prob * p_correct
                        new_prob_map[i][j] += prob * p_stay
                    elif movement == "right" and j + 1 < CELLCOLS:
                        new_prob_map[i][j + 1] += prob * p_correct
                        new_prob_map[i][j] += prob * p_stay
                    elif movement == "backward" and i - 1 >= 0:
                        new_prob_map[i - 1][j] += prob * p_correct
                        new_prob_map[i][j] += prob * p_stay
                    else:
                        new_prob_map[i][j] += prob

        total_prob = sum(sum(row) for row in new_prob_map)
        if total_prob > 0:
            for i in range(CELLROWS):
                for j in range(CELLCOLS):
                    new_prob_map[i][j] /= total_prob

        self.prob_map = new_prob_map

    def run(self):
        if self.status != 0:
            print("Conexão recusada ou erro")
            quit()

        stopped_state = 'run'
        print("Robô iniciado")

        self.readSensors()
        self.updateLocalization()  # Inicializar localização

        while True:
            self.readSensors()

            if self.measures.endLed:
                print(self.rob_name + " saindo")
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
        center_id = 0  # Sensor frontal
        left_id = 1    # Sensor esquerdo
        right_id = 2   # Sensor direito
        FRONT_THRESHOLD = 3.0

        if self.state == 'run':
            if self.measures.irSensor[center_id] > FRONT_THRESHOLD:
                if self.measures.irSensor[left_id] < self.measures.irSensor[right_id]:
                    # Girando à esquerda
                    self.state = 'rotate_left'
                else:
                    # Girando à direita
                    self.state = 'rotate_right'
            else:
                # Movendo para frente
                self.applyMotionModel("forward")  # Aplicar modelo de movimento antes de mover
                self.driveMotors(0.1, 0.1)
                self.distance_sum += 0.1

                # Verificar se o robô percorreu o comprimento de uma célula
                if int(self.distance_sum) % 2 == 0 and self.distance_sum >= 2.0:
                    print(f"Alcançou o centro da célula com distância acumulada: {self.distance_sum}")
                    self.updateLocalization()
                    self.distance_sum -= 2.0

        elif self.state == 'rotate_left':
            self.applyMotionModel("left")
            self.driveMotors(-0.05, 0.05)  # Girar à esquerda
            time.sleep(1.5)
            self.driveMotors(0.0, 0.0)
            self.state = 'run'

        elif self.state == 'rotate_right':
            self.applyMotionModel("right")
            self.driveMotors(0.05, -0.05)  # Girar à direita
            time.sleep(1.5)
            self.driveMotors(0.0, 0.0)
            self.state = 'run'

if __name__ == '__main__':
    rob_name = "pClient1"
    host = "localhost"
    pos = 1

    rob = MyRob(rob_name, pos, [0.0, 90.0, -90.0, 180.0], host)
    rob.setMap(labMap)
    rob.run()
