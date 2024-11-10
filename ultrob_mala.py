import sys
from croblink import *
from math import *
import xml.etree.ElementTree as ET
import time

CELLROWS = 7
CELLCOLS = 14
CELL_SIZE = 2  # Dimensione lato cella
CENTER_MARGIN = 0.2  # Margine di tolleranza per considerare il centro

class MyRob(CRobLinkAngs):
    def __init__(self, rob_name, rob_id, angles, host):
        CRobLinkAngs.__init__(self, rob_name, rob_id, angles, host)
        self.prob_map = [[1.0 / (CELLROWS * CELLCOLS)] * CELLCOLS for _ in range(CELLROWS)]
        self.state = 'stop'  # Stati: 'stop', 'run', 'rotate_left', 'rotate_right'

    def setMap(self, labMap):
        self.labMap = labMap

    def printMap(self):
        for l in reversed(self.labMap):
            print(''.join([str(l) for l in l]))

    def getExpectedMeasures(self, i, j):
        # Restituisce i valori attesi dei sensori per la cella (i, j)
        return [0.5, 0.5, 0.5, 0.5]  # Placeholder: da sostituire con valori specifici

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

        # Normalizzazione della distribuzione
        total_prob = sum(sum(row) for row in updated_probs)
        for i in range(CELLROWS):
            for j in range(CELLCOLS):
                updated_probs[i][j] /= total_prob

        self.prob_map = updated_probs

        # Stampa e salva la distribuzione in localization.out
        with open("localization.out", "a") as f:
            for row in reversed(self.prob_map):
                line = " ".join(f"{p:.4f}" for p in row)
                print(line)
                f.write(line + "\n")
            f.write("\n")

    def run(self):
        if self.status != 0:
            print("Connection refused or error")
            quit()

        stopped_state = 'run'

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

            # Controlla se il robot è al centro di una cella per aggiornare la localizzazione
            if self.isAtCellCenter():
                self.updateLocalization()

    def isAtCellCenter(self):
        # Verifica se il robot è al centro di una cella con tolleranza
        x, y = self.measures.x, self.measures.y
        cell_x = round((x - 1) / CELL_SIZE)
        cell_y = round((y - 1) / CELL_SIZE)
        center_x = cell_x * CELL_SIZE + 1
        center_y = cell_y * CELL_SIZE + 1
        return abs(x - center_x) < CENTER_MARGIN and abs(y - center_y) < CENTER_MARGIN

    def wander(self):
        center_id = 0
        left_id = 1
        right_id = 2

        # Soglia per considerare un ostacolo davanti
        FRONT_THRESHOLD = 3.0

        if self.state == 'run':
            # Se il sensore frontale rileva un ostacolo
            if self.measures.irSensor[center_id] > FRONT_THRESHOLD:
                # Confronta i sensori sinistro e destro per decidere la direzione
                if self.measures.irSensor[left_id] < self.measures.irSensor[right_id]:
                    print('Ostacolo davanti, fermo e ruota a sinistra')
                    self.state = 'rotate_left'
                else:
                    print('Ostacolo davanti, fermo e ruota a destra')
                    self.state = 'rotate_right'
            else:
                # Nessun ostacolo rilevato, procedi in avanti
                print('Percorso libero, vai avanti')
                self.driveMotors(0.1, 0.1)

        elif self.state == 'rotate_left':
            # Ruota a sinistra di 90°
            self.driveMotors(-0.1, +0.1)
            time.sleep(1.5)  # Tempo necessario per completare una rotazione di 90°
            self.driveMotors(0.0, 0.0)  # Fermati dopo la rotazione
            self.state = 'run'

        elif self.state == 'rotate_right':
            # Ruota a destra di 90°
            self.driveMotors(+0.1, -0.1)
            time.sleep(1.5)  # Tempo necessario per completare una rotazione di 90°
            self.driveMotors(0.0, 0.0)  # Fermati dopo la rotazione
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
