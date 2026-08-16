# StayStill: a large-scale 3d idle animation dataset

[![Project page](https://img.shields.io/badge/Project%20page-blue?style=plastic)](https://enekoassets.github.io/staystill.html)
[![Paper preprint](https://img.shields.io/badge/Paper%20preprint-green?style=plastic)](https://arxiv.org/abs/2605.13693)
[![Dataset](https://img.shields.io/badge/Dataset-yellow?style=plastic)](https://zenodo.org/records/18741736)
[![Video](https://img.shields.io/badge/Video-red?style=plastic)](https://www.youtube.com/watch?v=lhWebn_zrac)

<img width="2354" height="858" alt="showcase" src="https://github.com/user-attachments/assets/ec1a2986-509c-4c3c-8368-666dd195c766" />

## 🧭 About
**Data:** This repository contains the animation data presented in our paper [StayStill: a large-scale 3D idle animation dataset](https://arxiv.org/abs/2605.13693). StayStill is a dataset that contains around 650.000 frames of idle motion, encompassing general idle motion, idle motion while using a phone and idle actions. A more detailed overview of the data is explained in the **Data** section and in the original paper.

**Model:** It also contains the presented idle animation generator model: on the one hand, it contains the pretrained neural network from Qin et al. ([Paper](https://dl.acm.org/doi/10.1145/3550454.3555454), [GitHub repository](https://github.com/victorqin/motion_inbetweening)). On the other hand, it also contains the technique used to use this motion in-betweening network as an idle animation generator, as explained in the paper.

**Code:** Finally, it contains the evaluation code to reproduce the numerical and user-based comparisons, as well as the necessary responses from the user study to do so.

**Project page:** The project page can be found [here](https://enekoassets.github.io/staystill.html).
## 📖 Citing
If you use the StayStill dataset in any of your projects and scientific research, please cite it as follows:
```bibtex
@article{landa2026staystill,
  author = {Atxa Landa, Eneko and Rodriguez, Igor and Lazkano, Elena and Kucherenko, Taras},
  title = {StayStill: a large-scale 3D idle animation dataset},
  journal = {Computer Graphics Forum},
  year = {2026}
}
```

## 🧍‍♂️Data

https://github.com/user-attachments/assets/77879a49-c70e-42c1-a4e6-d339069f3bbb

### Dowloading
The dataset contains BVH files for all the animations. If you just need the data, you can download it from [Zenodo](https://zenodo.org/records/18741736).

### Train, validation and test splits
The official train, validation and test splits, as determined in our paper, are the following:
| Split | Subjects |
|:---|:---:|
| Train | 0 1 3 4 5 7 11 12 13 14 16 17 18 20 24 25 26 27 29 30 31 32 33 34 35 36 37 39 41 42 44 46 47 48 49 |
| Validation | 8 19 21 38 40 |
| Test | 2 6 9 10 15 22 23 28 43 45 |
### Cleaning the data
#### Manual cleaning
To easily clean the data, [bvhTools](https://github.com/Enekoassets/bvhTools) must be installed.
```
pip install bvhTools
```

Unzip the downloaded dataset, and locate it in the ``dataset`` folder. The idle animations part of the dataset contains shaky and incorrect motion due to bad detection of the motion capture system. These incorrect parts can be removed by running the ``cleanData.py`` script in the scripts folder.

```
cd StayStill/scripts
python3 cleanData.py
```

This script will remove the parts from the long idle animations, and it will create smaller pieces from the original animation with the correct parts of the long sequence. For example, ``idle_00`` might be split into ``idle_00_1``, ``idle_00_2`` and ``idle_00_3`` after removing 2 incorrect parts. The cleaned data will be put inside new folders: ``freemocap_clean/idle`` and ``lafan_clean/idle``.

#### Automatic cleaning
To clean the data in an automatic manner, the `autoCleanData.py` script can be used. It also needs `bvhTools` to be installed and the dataset located in the `dataset` folder. This script measures the joint speeds in the dataset. Then, it detects speeds 5 standard deviations away from the mean. It expands the detections 10 frames to each side and removes those parts. Finally, it also discards sections that are smaller than the `min_len` variable.

To use the script, set the following variables inside the script and then run it:
```python
dataset_folder = "./dataset/idle" # Change the folder path if you want to clean other subsets of the data
output_folder = "./dataset/idle_auto_clean"

threshold = 5  # Z-score threshold (instances that are 5 std away from the mean are detected as outliers. Change this number for a more relaxed/strict removal.)
min_len = 60 # sections that are smaller than this number will also be discarded from the final clean dataset
```

### Detail
The data is divided into 2 folders:
- **Freemocap**: It contains the original skeleton provided by Freemocap (without the finger bones) (a)
- **Lafan**: It contains the data retargeted and fitted to the LaFAN1 skeleton. (b)

![figure](media/skeletonComparison.png)

Each of these two folders has 3 subfolders:
- **Idle**: Contains 2 minutes long sequences of people idling
- **Phone**: Contains 2 minutes long sequences of people idling while using a phone
- **Actions**: Contains 18 different actions that are typical in idle scenarios

Each animation clip is named as so:

action_name[\_take_number]\_person_ID.bvh

The following table presents the data in a more specific manner:

| Motion Type | Action Name | Nº of frames | Duration (hh:mm:ss) | Nº of clips
|:---|:---:|:---:|:---:|:---:|
| Idle action: look up/sky  | l_up | 27.943 | 15:31 | 98 |
| Idle action: look around  | l_aro | 20.338 | 11:17 | 92 |
| Idle action: look down/floor  | l_dow | 17.817 | 09:53 | 85 |
| Idle action: look shoes  | l_sho | 15.623 | 08:40 | 75 |
| Idle action: check watch  | l_wat | 11.332 | 06:17 | 92 |
| Idle action: check phone  | l_pho | 21.237 | 11:47  | 89 |
| Idle action: scratch head  | sc_hea | 13.199 | 07:19 | 92 |
| Idle action: scratch arm  | sc_arm | 13.750 | 07:38 | 93 |
| Idle action: scratch leg  | sc_leg | 11.510 | 06:23 | 77 |
| Idle action: scratch back  | sc_bac | 10.900 | 06:03 | 66 |
| Idle action: touch face/chin  | t_fac | 14.852 | 08:15 | 93 |
| Idle action: stretch arms  | st_arm | 14.473 | 08:02 | 80 |
| Idle action: stretch back  | st_bac | 12.300 | 06:50 | 71 |
| Idle action: rub eyes  | sc_eye | 15.430 | 08:34 | 97 |
| Idle action: yawn  | yaw | 13,766 | 07:38 | 95 |
| Idle action: look back (left)  | lb_lef | 10.253 | 05:41 | 69 |
| Idle action: look back (right)  | lb_rig | 10.571 | 05:52 | 75 |
| Idle action: change balance left -> right  | wei_lr | 11.100 | 06:10 | 48 |
| Idle action: change balance right -> left | wei_rl | 9.357 | 05:11 | 47 |
| **Idle actions total** | -- | **275.751** | **2:33:11** | **1534** |
| **General Idle** | idle | **181.846** | **1:41:01** | **50** |
| **Idle with a phone** | phone | **187.741** | **1:44:18** | **50** |

## 🧍‍♀️ Idle animation generator model
The repository also contains the idle generator model described in the paper. The generator has been used to compare a deep learning baseline with other naive baselines, so it generates motion taking a ground truth (GT) motion clip as base motion. It samples the GT every 45 frames, and interpolates between those frames using the in-betweening neural network by Qin et al.

### Prerequisites
- Install necessary packages (use your virtual environment of choice):
```
pip install scipy argparse torch
```
  
- Install [Blender 4](https://www.blender.org/). *Note: Blender 5 won't directly work. The next snap installation should work out of the box:*
```
sudo snap install blender --channel=4.5lts/stable --classic
```
   
- Clone this repository into a folder of your choice.
```
git clone https://github.com/Enekoassets/StayStill.git
```
- Clone the motion [in-betweening via two stage transformers repository](https://github.com/victorqin/motion_inbetweening) from Qin et al. **to the same folder (important)**.
```
git clone https://github.com/victorqin/motion_inbetweening.git
```
Your folder structure should look like this:
```
folder_of_your_choice
├── StayStill
│   ├── configs
│   ├── dataset
│   ├── scripts
│   └── README.md
└── motion_inbetweening
    ├── configs
    ├── datasets
    ├── experiments
    └── ...
```

- Download the dataset from [Zenodo](https://zenodo.org/records/18741736), and unzip the contents (don't use data cleaning script, use the raw data from Zenodo, or the indexing will not work properly). Then, copy the ``lafan`` folder from the dataset in the ``datasets`` folder in the motion_inbetweening ``(MIB)`` repository.

- Download the pretrained models from the [releases](https://github.com/Enekoassets/StayStill/releases/tag/Model) section of this repository.
  
- Unzip the ``models.zip`` file and paste the ``idle_ctx_model`` and ``idle_det_model`` folders into the ``experiments`` folder in the ``MIB`` repository.

- Run the ``setup.py`` script in the scripts folder. It will copy the necessary files from the staystill repository to the ``MIB`` repository.
```
cd StayStill/scripts
python3 setup.py
```

### Running the generator
First locate yourself in the ``motion_inbetweening/scripts`` folder.
```
cd motion_inbetweening/scripts
```
Run the ``generatorLogic.py`` script to generate all the transitions. This script will create a folder called json, and it will save the motion there, in JSON format. You have to pass the **index** of the ground truth that will be used to generate the new motion from.

You can also pass ``--generateSlerp`` and ``--generateEasing`` as additional arguments, to also generate motion using these baselines.

```python
python3 generatorLogic.py -i 7
```

After this, the output has to be converted into the bvh format. Run the ``json2bvhMotion.py`` script. It will read every json in the json folder and it will write the corresponding BVH files in a newly created ``bvh`` folder.

```python
python3 json2bvhMotion.py
```

Finally, run the ``blenderPostProcess.py`` to apply the post-processing described in the paper. This will read all the BVH files in the ``bvh`` folder and it will prepare the final post processed animations. This postprocessed animations will be written into the same ``bvh`` folder, with the subscript ``_pp``.

```python
python3 blenderPostProcess.py
```

*Note: If bpy is not correctly identified, you may run the script directly with blender from the terminal. Blender 4.5 installed using snap has been tested:*
```bash
sudo snap install blender --channel=4.5lts/stable --classic
```
```bash
blender --background --python blenderPostProcess.py
```

Now, you can visualize the generated idle motion in any visualization engine, like [Blender](https://www.blender.org/), [bvhView](https://theorangeduck.com/media/uploads/BVHView/bvhview.html) or using the visualization functionalities of the newly installed [bvhTools](https://github.com/Enekoassets/bvhTools/), with the following small python script.

```python
from bvhTools.bvhIO import readBvh
from bvhTools.bvhVisualizer import showBvhAnimation

path = "path_to_bvh_file"
bvh = readBvh(path)
showBvhAnimation(bvh)
```

## 📋 Evaluation code
### 📏 Numerical evaluation
#### Model results
In the numerical evaluation, you can compare the pretrained neural network, or train your own neural network on the motion in-betweening task using StayStill. Then, you can test your network using the provided evaluation script. This is a modified version of the original evaluation script in the ``MIB`` repository. 

*Note: The [prerequisites](#prerequisites) have to be filled in order to use this.*

- First locate yourself in the ``motion_inbetweening/scripts`` folder.
```
cd motion_inbetweening/scripts
```

- You can use the following command to run the script with the flag -t 99 (this will trigger all transition sizes 5, 15, 30, 45):

```python
python3 eval_detail_model_mod.py idle_det_model idle_ctx_model -t 99
```

This will provide the results obtained by the model.

#### Baseline results
To calculate the baseline results, the process is exactly the same as with the model results, but running the modified ``run_baseline_benchmark_mod.py`` script, based on the original one provided by Qin et al. The modified script also integrates the results of the SLERP-Q (slerp with quadratic ease-in-out easing).

*Note: The [prerequisites](#prerequisites) have to be filled in order to use this.*

- First locate yourself in the ``motion_inbetweening/scripts`` folder.
```
cd motion_inbetweening/scripts
```

- Run the script
```python
python3 run_baseline_benchmark_mod.py idle_ctx_model
```

This way you can obtain the results of the baselines in the same testing subset of that the model is tested on, and compare these results with the results from the model.

### 🤨 User-based evaluation
User-based evaluation is much simpler to perform. 

- You need to install the necessary packages (use your virtual environment of choice): 
```bash
pip install pandas numpy scikit-learn tqdm matplotlib openpyxl
```

- First locate yourself in the ``StayStill/scripts`` folder.
```
cd StayStill/scripts
```

- Then, to reproduce the results from the paper, just run the ``subjectiveEvaluation.py`` script in the ``scripts`` folder. This will read the results from the user study from the xlsx file, and will output the Elo ranking, the win rates, and will perform the bootstrap process described in the paper.
```
python3 subjectiveEvaluation.py
```

## 📋 License
The provided dataset and code in this repository is released under the **MIT License**.  
You are free to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the dataset, under the conditions outlined in the MIT License.

See [LICENSE.txt](LICENSE.txt) for full license text.
