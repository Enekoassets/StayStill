import json
from scipy.spatial.transform import Rotation as R
import argparse as ap
import os

parser = ap.ArgumentParser()
parser.add_argument("--jsonFolder", type=str, default="./json/")
parser.add_argument("--bvhFolder", type=str, default="./bvh/")
parser.add_argument("--bvhStructure", type=str, default="baseStructure.bvh")
args = parser.parse_args()

baseJsonPath = args.jsonFolder
baseBvhPath = args.bvhFolder
baseStructurepath = args.bvhStructure

baseStructure = ""
with open(baseStructurepath, "r") as f:
    baseStructure = f.readlines()

for file in os.listdir(baseJsonPath):
    if file.endswith(".json"):
        jsonPath = os.path.join(baseJsonPath, file)
        bvhPath = os.path.join(baseBvhPath, file.strip(".json") + ".bvh")
    if(os.path.exists(bvhPath)):
        continue
    # Load JSON file
    with open(jsonPath, "r") as jsonFile:
        jsonString = jsonFile.readlines()
        file = json.loads(jsonString[0])
    
    # Extract positions
    posData = file["positions"]
    rotData = file["rotations"]
    
    bvhPosData = []
    bvhRotData = []
    for positions, rotations in zip(posData, rotData):
        bvhPosData.append(positions[0])
        # The 'zyx' orientation is for the LAFAN1 files. If you BVH file has another orientation, change this line
        bvhRotData.append([R.from_matrix(x).as_euler('XYZ', degrees=True) for x in rotations])

    with open(bvhPath, "w") as f:
        for line in baseStructure:
            if "XXXX" in line:
                line = line.replace("XXXX", str(len(bvhPosData)))
            f.write(line)
        for pos, rots in zip(bvhPosData, bvhRotData):
            f.write(' '.join(f'{x:.6f}' for x in pos) + " ")
            for rot in rots:
                f.write(' '.join(f'{float(x):.6f}' for x in rot) + " ")
            f.write("\n")

print("Converted JSON files to BVH files")
