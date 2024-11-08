import sys
from croblink import *  # Importa la libreria per controllare il robot
import math
import numpy as np
import xml.etree.ElementTree as ET  # Libreria per la gestione di file XML

# manca centramento cella, manca calcolo probabilità corretto
CELLROWS = 7
CELLCOLS = 14
sigma = 0.1 # standard deviation = sensors noise
pi = math.pi

class MyRob(CRobLinkAngs):
    def __init__(self, rob_name, rob_id, angles, host):
        CRobLinkAngs.__init__(self, rob_name, rob_id, angles, host)
        self.prob_dist = self.initialize_probability()
        self.labMap = None  # Inizializzazione della mappa

    def initialize_probability(self):
        # Inizializza la distribuzione di probabilità uniforme
        return np.full((CELLROWS, CELLCOLS), 1.0 / (CELLROWS * CELLCOLS))

    def setMap(self, labMap):
        # Imposta la mappa
        self.labMap = labMap

    def printMap(self):
        # Stampa la mappa attuale sul terminale per visualizzare la griglia
        for l in reversed(self.labMap):
            print(''.join([str(l) for l in l]))

    def print_probability_distribution(self):
        for row in self.prob_dist:
            print(' '.join(f"{x:.4f}" for x in row))

    def run(self):
        if self.status != 0:
            print("Connection refused or error")
            quit()

        state = 'stop'
        stopped_state = 'run'

        while True:
            self.readSensors()
            if self.measures.endLed:
                print(self.rob_name + " exiting")
                quit()

            if state == 'stop' and self.measures.start:
                state = stopped_state
            if state != 'stop' and self.measures.stop:
                stopped_state = state
                state = 'stop'

            if state == 'run':
                self.print_probability_distribution()  # Stampa la distribuzione di probabilità
                self.wander()  # Movimento casuale del robot

    def wander(self):
        center_id, left_id, right_id, back_id = 0, 1, 2, 3
        if (self.measures.irSensor[center_id] > 5.0 or
            self.measures.irSensor[left_id] > 5.0 or
            self.measures.irSensor[right_id] > 5.0 or
            self.measures.irSensor[back_id] > 5.0):
            print('Rotate left')
            self.driveMotors(-0.1, +0.1)
        elif self.measures.irSensor[left_id] > 2.7:
            print('Rotate right')
            self.driveMotors(+0.1, -0.1)
        elif self.measures.irSensor[right_id] > 2.7:
            print('Rotate left')
            self.driveMotors(-0.1, +0.1)
        else:
            print('Go')
            self.driveMotors(0.1, 0.1)

class Map():
    def __init__(self, filename):
        tree = ET.parse(filename)
        root = tree.getroot()
        self.labMap = [[' '] * (CELLCOLS * 2 - 1) for _ in range(CELLROWS * 2 - 1)]
        for child in root.iter('Row'):
            line = child.attrib['Pattern']
            row = int(child.attrib['Pos'])
            if row % 2 == 0:
                for c in range(len(line)):
                    if (c + 1) % 3 == 0 and line[c] == '|':
                        self.labMap[row][(c + 1) // 3 * 2 - 1] = '|'
            else:
                for c in range(len(line)):
                    if c % 3 == 0 and line[c] == '-':
                        self.labMap[row][c // 3 * 2] = '-'

if __name__ == '__main__':
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

    rob = MyRob(rob_name, pos, [0.0, 90.0, -90.0, 180.0], host)
    if mapc is not None:
        rob.setMap(mapc.labMap)
        rob.printMap()

    rob.run()
