import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
package_root = os.path.join(project_root, "packages")
sys.path.append(package_root)

from motion_inbetween.model import ContextTransformer, DetailTransformer
from motion_inbetween.config import load_config_by_name
from motion_inbetween.train import context_model as ctx_mdl
from motion_inbetween.train import detail_model as det_mdl
from motion_inbetween.data import bvh, utils_np
from motion_inbetween.data import utils_torch as data_utils
from scipy.spatial.transform import Rotation as R, Slerp
from motion_inbetween import visualization
from motion_inbetween.train import utils as train_utils
from scipy.spatial.transform import Rotation as R
import numpy as np
import torch
import math
import argparse as ap
import os

class Generator:
    def __init__(self, contextModel, detailModel, transitionSize, index):
        self.ctxConfig = load_config_by_name(contextModel)
        self.detConfig = load_config_by_name(detailModel)
        self.transitionSize = transitionSize
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.detailModel = DetailTransformer(self.detConfig["model"]).to(self.device)
        self.contextModel = ContextTransformer(self.ctxConfig["model"]).to(self.device)
        self.index = index
        train_utils.load_checkpoint(self.detConfig, self.detailModel, suffix=".min")
        train_utils.load_checkpoint(self.ctxConfig, self.contextModel, suffix=".min")
        self.loadSequence()
        os.makedirs("json", exist_ok=True)
        os.makedirs("bvh", exist_ok=True)

    def loadSequence(self):
        print(f"Loading ground truth sequence: ../datasets/lafan/idle/idle_{str(self.index).zfill(2)}.bvh")
        self.positionsA, self.rotationsA, self.global_positionsA, self.global_rotationsA, self.foot_contactA, self.framesA, self.parentsA = self.load_bvh_file(f"../datasets/lafan/idle/idle_{str(self.index).zfill(2)}.bvh")
    
    def _to_tensor(self, array):
        return torch.tensor(array, dtype=torch.float32, device=self.device)
    
    def load_bvh_file(self, bvhPath):
        f = os.path.abspath(os.path.join(bvhPath))
        if f.endswith(".bvh"):
            file_name = os.path.basename(f).rsplit(".", 1)[0]
            seq_name, actor = file_name.rsplit("_", 1)
        print("Processing file {}".format(bvhPath))
        positions = []
        rotations = []
        global_positions = []
        global_rotations = []
        foot_contact = []
        frames = []
        anim = bvh.load_bvh(bvhPath, start=0)
        # global joint rotation, position
        gr, gp = utils_np.fk(anim.rotations, anim.positions, anim.parents)

        # left, right foot contact
        cl, cr = utils_np.extract_feet_contacts(
            gp, [3, 4], [7, 8], vel_threshold=0.2)

        positions.append(self._to_tensor(anim.positions))
        rotations.append(self._to_tensor(anim.rotations))
        global_positions.append(self._to_tensor(gp))
        global_rotations.append(self._to_tensor(gr))
        foot_contact.append(self._to_tensor(
            np.concatenate([cl, cr], axis=-1)))
        frames.append(anim.positions.shape[0])
        parents = anim.parents
        return positions, rotations, global_positions, global_rotations, foot_contact, frames, parents

    def ease_in_out_quad(self, t):
        return np.where(t < 0.5, 2 * t**2, 1 - (-2 * t + 2)**2 / 2)

    def generateSlerp(self, easing = False):
        initialContext = 10
        transitionSize = self.transitionSize
        newPositions = [x for x in self.positionsA[0][0:initialContext]]
        newRotations = [x for x in self.rotationsA[0][0:initialContext]]
        positionTargets = [x for i, x in enumerate(self.positionsA[0][initialContext:]) if i % transitionSize == 0]
        rotationTargets = [x for i, x in enumerate(self.rotationsA[0][initialContext:]) if i % transitionSize == 0]

        for target in range(len(positionTargets)-1):
            for frame in range(transitionSize):
                if(easing):
                    newPositions.append(torch.lerp(positionTargets[target], positionTargets[target+1], np.ndarray.item(self.ease_in_out_quad(frame/transitionSize))))
                else:    
                    newPositions.append(torch.lerp(positionTargets[target], positionTargets[target+1], frame/transitionSize))

        interpolatedRotations = []
        interpolatedRotationsList = []
        for target in range(len(rotationTargets)-1):
            listtarget = rotationTargets[target].tolist()
            listtargetnext = rotationTargets[target+1].tolist()

            for rotationIndex in range(0, len(listtarget)):
                r1 = R.from_matrix(listtarget[rotationIndex])
                r2 = R.from_matrix(listtargetnext[rotationIndex])
                slerp = Slerp([0, 1], R.concatenate([r1, r2]))
                times = np.linspace(0, 1, transitionSize)
                if(easing):
                    times = self.ease_in_out_quad(times)
                interpolatedRotationsList.append(slerp(times).as_matrix())
            interpolatedRotations.append(interpolatedRotationsList)
            interpolatedRotationsList = []

        interpolatedRotations = np.moveaxis(interpolatedRotations, 2, 1)
        for transition in interpolatedRotations:
            newRotations.extend(torch.from_numpy(transition).to(self.device))

        newPositions = torch.stack(newPositions)
        newRotations = torch.stack(newRotations)
        if(easing):
            json_path_gt = f"./json/{str(self.index).zfill(2)}_easing.json"
        else:
            json_path_gt = f"./json/{str(self.index).zfill(2)}_slerp.json"
        visualization.save_data_to_json(
            json_path_gt, newPositions, newRotations,
            self.foot_contactA[0], self.parentsA)
        if(easing):
            print("Saved SLERP-Quad easing sequence")
        else:
            print("Saved SLERP sequence")
    
    def generate(self):
        indices = self.detConfig["indices"]
        initialContext = 10
        allInferences = []
        for targetIndex in range(0, math.floor((len(self.positionsA[0])-initialContext)/self.transitionSize)-1):
            target_idx = initialContext + self.transitionSize
            seq_slice = slice(initialContext, target_idx)
            window_len = initialContext + self.transitionSize + 2
            dtype = torch.float32

            # attention mask for context model
            atten_mask_ctx = ctx_mdl.get_attention_mask(
                window_len, initialContext, target_idx, self.device)
            # attention mask for detail model
            atten_mask = det_mdl.get_attention_mask(window_len, target_idx, self.device)

            mean_ctx, std_ctx = ctx_mdl.get_train_stats_torch(
                self.ctxConfig, dtype, self.device)
            mean_state, std_state, _, _ = \
                det_mdl.get_train_stats_torch(self.detConfig, dtype, self.device)

            positionsA = self.positionsA[0].to(self.device)
            rotationsA = self.rotationsA[0].to(self.device)
            foot_contactA = self.foot_contactA[0].to(self.device)

            positions = positionsA[..., self.transitionSize*targetIndex:self.transitionSize*targetIndex+window_len, :, :]
            rotations = rotationsA[..., self.transitionSize*targetIndex:self.transitionSize*targetIndex+window_len, :, :, :]
            foot_contact = foot_contactA[..., self.transitionSize*targetIndex:self.transitionSize*targetIndex+window_len, :]
            print(self.transitionSize*targetIndex, self.transitionSize*targetIndex+window_len)
            positions = positions.unsqueeze(0)
            rotations = rotations.unsqueeze(0)
            foot_contact = foot_contact.unsqueeze(0)
            positions, rotations = data_utils.to_start_centered_data(
                positions, rotations, initialContext)
            pos_new, rot_new, foot_contact_new = det_mdl.evaluate(
                self.detailModel, self.contextModel,
                positions, rotations, foot_contact, seq_slice, indices,
                mean_ctx, std_ctx, mean_state, std_state,
                atten_mask, atten_mask_ctx, False)

            allInferences.append((pos_new, rot_new, foot_contact_new))

        pos_new, rot_new, foot_contact_new = zip(*allInferences)
        pos_new = torch.cat(pos_new, dim=0)
        rot_new = torch.cat(rot_new, dim=0)
        foot_contact_new = torch.cat(foot_contact_new, dim=0)
        pos_new = list(pos_new)
        rot_new = list(rot_new)
        for i, (position, rotation) in enumerate(zip(pos_new, rot_new)):
            pos_new[i] = position[10:-2]
            rot_new[i] = rotation[10:-2]

        pos_new = torch.stack(pos_new)
        rot_new = torch.stack(rot_new)
        pos_new = pos_new.reshape(1, -1, 22, 3)
        rot_new = rot_new.reshape(1, -1, 22, 3, 3)
        foot_contact_new = foot_contact_new.reshape(1, -1, 4)

        json_path_gt = f"./json/{str(self.index).zfill(2)}_gt.json"
        visualization.save_data_to_json(
            json_path_gt, positionsA, rotationsA,
            foot_contactA, self.parentsA)

        json_path = f"./json/{str(self.index).zfill(2)}_gen.json"
        
        visualization.save_data_to_json(
            json_path, pos_new[0], rot_new[0],
            foot_contact_new[0], self.parentsA)
        print("Saved JSON files.")

if __name__ == "__main__":
    transitionSize = 45
    args = ap.ArgumentParser()
    args.add_argument("--index", "-i", type=int, default=-1)
    args.add_argument("--generateSlerp", action="store_true")
    args.add_argument("--generateEasing", action="store_true")
    args = args.parse_args()
    gtIndex = args.index
    generateSlerp = args.generateSlerp
    generateEasing = args.generateEasing
    if(gtIndex == -1):
        print("Usage: python generatorLogic.py -i <index>")
        exit()
    generator = Generator("idle_ctx_model", "idle_det_model", transitionSize, gtIndex)
    if generateSlerp:
        generator.generateSlerp(easing=False)
    if generateEasing:
        generator.generateSlerp(easing=True)
    generator.generate()