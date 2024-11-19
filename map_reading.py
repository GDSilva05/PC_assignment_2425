import xml.etree.ElementTree as ET

def parse_lab_file(file_path):
    # Carica l'XML
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Trova tutte le righe (Row)
    rows = root.findall("Row")
    max_width = int(root.get("Width"))
    
    # Ordina le righe in base alla posizione (Pos) decrescente
    rows_sorted = sorted(rows, key=lambda x: int(x.get("Pos")), reverse=True)
    
    patterns = []
    
    for row in rows_sorted:
        pattern_str = row.get("Pattern")  # Legge il pattern della riga
        # Crea una lista di caratteri dalla stringa del pattern
        pattern_list = list(pattern_str.ljust(max_width, ' '))
        patterns.append(pattern_list)  # Aggiunge la riga al pattern
    
    return patterns

# Esempio di utilizzo
file_path = "/home/mala/ciberRatoTools/Labs/PathFinder/pathFinderCorridor.xml" #Labs/PathFinder/pathFinderCorridor.xml
patterns = parse_lab_file(file_path)

# Stampa i patterns
for pattern in patterns:
    print(pattern)
