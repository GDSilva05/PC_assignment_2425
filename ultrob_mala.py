import sys
from croblink import *
from math import *
import xml.etree.ElementTree as ET
import time

CELLROWS = 7
CELLCOLS = 14
CELL_SIZE = 2  # Dimensione lato cella
ROBOT_DIAM = 1.0     # Diametro del robot
NOISE = 0.0          # Noise è 0, ma la formula lo include per estensione

class MyRob(CRobLinkAngs):
    def __init__(self, rob_name, rob_id, angles, host):
        CRobLinkAngs.__init__(self, rob_name, rob_id, angles, host)
        self.prob_map = [[1.0 / (CELLROWS * CELLCOLS)] * CELLCOLS for _ in range(CELLROWS)]
        self.state = 'stop'
        
        self.distance_sum = 0.0  # Somma delle distanze percorse
        self.out_left = 0.0  # Potenza effettiva applicata al motore sinistro al tempo t-0 (inizialmente fermo)
        self.out_right = 0.0  # Potenza effettiva applicata al motore destro al tempo t-0 (inizialmente fermo)
        
        # Attributi per i valori di input dei motori e l'angolo di rotazione
        self.in_left_t = 0.0
        self.in_right_t = 0.0
        self.theta = 0.0  # Orientamento del robot al tempo t=0

    def setMap(self, labMap):
        self.labMap = labMap

    def printMap(self):
        for l in reversed(self.labMap):
            print(''.join([str(l) for l in l]))

    def getExpectedMeasures(self, i, j):
        return [0.5, 0.5, 0.5, 0.5]  # Placeholder

    def gaussian_prob(self, mu, sigma, x):
        return (1.0 / (sqrt(2 * pi) * sigma)) * exp(-0.5 * ((x - mu) ** 2) / (sigma ** 2))

    def updateLocalization(self):
        sensor_readings = [
            self.measures.irSensor[0],
            self.measures.irSensor[1],
            self.measures.irSensor[2],
            self.measures.irSensor[3]
        ]
        
        updated_probs = []
        for i in range(CELLROWS):
            row_probs = []
            for j in range(CELLCOLS):
                prob = 1.0
                expected_measures = self.getExpectedMeasures(i, j)
                
                for sensor_value, expected_value in zip(sensor_readings, expected_measures):
                    prob *= self.gaussian_prob(expected_value, 0.1, sensor_value)

                row_probs.append(prob)
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

    def applyMovementModel(self):
        # Calcola `out_left` e `out_right` usando il filtro IIR con i valori di input e output al tempo t-1
        self.out_left = (self.in_left_t + self.out_left) / 2 * (1 + NOISE)
        self.out_right = (self.in_right_t + self.out_right) / 2 * (1 + NOISE)

        # Calcola la componente di traslazione (lin) e aggiorna `distance_sum`
        lin = (self.out_right + self.out_left) / 2
        self.distance_sum += lin

        # Calcola la componente di rotazione e aggiorna `theta`
        rot = (self.out_right - self.out_left) / ROBOT_DIAM
        self.theta += rot  # Aggiorna l'orientamento del robot

        # Utilizza una tolleranza per verificare se si è raggiunto un multiplo di 2 (cella successiva)
        if abs(self.distance_sum - round(self.distance_sum / 2) * 2) < 1e-2:
            print(f"Centro della cella raggiunto con distanza cumulativa: {self.distance_sum}")
            self.updateLocalization()
            self.distance_sum = 0.0  # Reset della distanza percorsa per la prossima cella

    def run(self):
        if self.status != 0:
            print("Connection refused or error")
            quit()

        stopped_state = 'run'
        print("Robot avviato")

        # Al tempo t=0, il robot è fermo e si trova al centro della cella
        self.readSensors()  # Legge i dati dai sensori per popolare self.measures
        self.updateLocalization()  # Ora possiamo calcolare la probabilità di localizzazione

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
                # Imposta i valori di input dei motori per il movimento in avanti
                self.in_left_t = 0.1
                self.in_right_t = 0.1
                self.applyMovementModel()
                self.driveMotors(self.in_left_t, self.in_right_t)

        elif self.state == 'rotate_left':
            self.in_left_t = -0.1
            self.in_right_t = 0.1
            self.applyMovementModel()
            time.sleep(1.5)
            self.driveMotors(0.0, 0.0)
            self.state = 'run'

        elif self.state == 'rotate_right':
            self.in_left_t = 0.1
            self.in_right_t = -0.1
            self.applyMovementModel()
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

rob_name = "pClient1"
host = "localhost"
pos = 1
mapc = None

for i in range(1, len(sys.argv), 2):
    if (sys.argv[i] == "--host" or sys.argv[i] == "-h") and i != len(sys.argv) - 1:
        host = sys.argv[i + 1]
    elif (sys.argv[i] == "--pos" or sys.argv[i] == "-p") and i != len(sys.argv) - 1:
        pos = int(sys.argv[i + 1])
    elif (sys.argv[i] == "--robname" or sys.argv[i] == "-r") and i != len(sys.argv) - 1:
        rob_name = sys.argv[i + 1]
    elif (sys.argv[i] == "--map" or sys.argv[i] == "-m") and i != len(sys.argv) - 1:
        mapc = Map(sys.argv[i + 1])
    else:
        print("Unknown argument", sys.argv[i])
        quit()

if __name__ == '__main__':
    rob = MyRob(rob_name, pos, [0.0, 90.0, -90.0, 180.0], host)
    if mapc is not None:
        rob.setMap(mapc.labMap)
        rob.printMap()
    
    rob.run()
