import os
from bvhTools import bvhIO, bvhMetrics, bvhSlicer
import numpy as np

# Expands mask from 27 to 69 channels
def expand_mask(mask):
    expanded_cols = []

    for j in range(mask.shape[1]):
        if j == 0:
            reps = 12  # special case for first channel group
        else:
            reps = 9  # all other channels

        expanded_cols.append(np.repeat(mask[:, j:j+1], reps, axis=1))

    return np.concatenate(expanded_cols, axis=1)

def extract_valid_segments(mask):
    frame_bad = np.any(mask, axis=1)
    frame_good = ~frame_bad

    fromFrames = []
    toFrames = []

    T = len(frame_good)

    in_segment = False

    for t in range(T):
        if frame_good[t] and not in_segment:
            start = t
            in_segment = True

        elif not frame_good[t] and in_segment:
            end = t - 1
            fromFrames.append(start)
            toFrames.append(end)
            in_segment = False

    if in_segment:
        fromFrames.append(start)
        toFrames.append(T - 1)

    return fromFrames, toFrames

dataset_folder = "./dataset/idle" # Change the folder path if you want to clean other subsets of the data
output_folder = "./dataset/idle_auto_clean"

threshold = 5  # Z-score threshold (instances that are 5 std away from the mean are detected as outliers. Change this number for a more relaxed/strict removal.)
min_len = 60 # sections that are smaller than this number will also be discarded from the final clean dataset

os.makedirs(output_folder, exist_ok=True)

for file in os.listdir(dataset_folder):
    if file.endswith(".bvh"):
        print(f"Processing {file}...")
        bvh = bvhIO.readBvh(os.path.join(dataset_folder, file))
        speeds = bvhMetrics.getSpeeds(bvh, type="magnitude")
        names_mask = [True if "EndSite" in name else False for name in list(bvh.skeleton.joints.keys())]
        speeds_fitered = speeds[:, ~np.array(names_mask)]

        # Compute Z-scores for all channels
        mean = np.mean(speeds_fitered, axis=0)
        std = np.std(speeds_fitered, axis=0)
        std[std == 0] = 1e-8  # avoid division by zero

        z_scores = (speeds_fitered - mean) / std
        outlier_mask = np.abs(z_scores) > threshold
        outlier_mask = np.concatenate([np.zeros((1, outlier_mask.shape[1]), dtype=bool), outlier_mask], axis=0)

        extend_num_frames = 10
        extended_outlier_mask = np.zeros_like(outlier_mask)
        for i in range(outlier_mask.shape[1]):
            for j in range(outlier_mask.shape[0]):
                if outlier_mask[j, i]:
                    extended_outlier_mask[max(0, j - extend_num_frames) : min(outlier_mask.shape[0], j + extend_num_frames), i] = True

        expanded_mask = expand_mask(extended_outlier_mask)

        fromFrames, toFrames = extract_valid_segments(expanded_mask)

        filtered_from = []
        filtered_to = []

        for f, t in zip(fromFrames, toFrames):
            if (t - f + 1) >= min_len:
                filtered_from.append(f)
                filtered_to.append(t)

        fromFrames, toFrames = filtered_from, filtered_to
        T = expanded_mask.shape[0]

        # total kept frames
        kept_frames = sum((t - f + 1) for f, t in zip(fromFrames, toFrames))

        lost_frames = T - kept_frames

        print(f"Total frames: {T}")
        print(f"Kept frames: {kept_frames}")
        print(f"Lost frames: {lost_frames}")
        print(f"Loss percentage: {100 * lost_frames / T:.2f}%")
        
        bvhPieces = bvhSlicer.getBvhSlices(bvh, fromFrames, toFrames)
        for i, piece in enumerate(bvhPieces):
            bvhIO.writeBvh(piece, os.path.join(output_folder, file.rstrip(".bvh") + f"_{i}.bvh"))