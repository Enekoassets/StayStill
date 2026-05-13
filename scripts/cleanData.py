from bvhTools import bvhIO, bvhSlicer
import os
import csv

parts = list(csv.reader(open("./removeParts.csv")))

def compute_good_ranges(length, bad_from, bad_to):
    bad_ranges = sorted(zip(bad_from, bad_to))
    good_from = []
    good_to = []
    start = 0

    for bad_start, bad_end in bad_ranges:
        if start < bad_start:
            good_from.append(start)
            good_to.append(bad_start - 1)
        start = max(start, bad_end + 1)

    if start <= length:
        good_from.append(start)
        good_to.append(length)

    return good_from, good_to


def process_folder(folder, outputFolder):
    os.makedirs(outputFolder, exist_ok=True)

    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".bvh") and "idle" in file:
                print(f"Cleaning: {file}")
                index = file.split("_")[0]
                in_path = os.path.join(root, file)

                badForFrames = [int(p[1]) for p in parts if index in p[0]]
                badToFrames = [int(p[2]) for p in parts if index in p[0]]

                bvh = bvhIO.readBvh(in_path)

                if badForFrames and badToFrames:
                    goodFrom, goodTo = compute_good_ranges(
                        bvh.motion.numFrames,
                        badForFrames,
                        badToFrames
                    )
                    slices = bvhSlicer.getBvhSlices(bvh, goodFrom, goodTo)

                    for i, slice in enumerate(slices):
                        out_name = f"{file[:-4]}_{i}.bvh"
                        bvhIO.writeBvh(slice, os.path.join(outputFolder, out_name))
                else:
                    out_name = f"{file[:-4]}_0.bvh"
                    bvhIO.writeBvh(bvh, os.path.join(outputFolder, out_name))


# Run for both datasets
process_folder("../dataset/lafan", "../dataset/lafan_cleaned/idle")
print("Cleaned LAFAN dataset")

process_folder("../dataset/freemocap", "../dataset/freemocap_cleaned/idle")
print("Cleaned FREEMOCAP dataset")