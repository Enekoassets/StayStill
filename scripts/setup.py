import shutil
import os
print("Copying necessary files to the motion in-betweening folder")
shutil.copyfile("./blenderPostProcess.py", "../../motion_inbetweening/scripts/blenderPostProcess.py")
shutil.copyfile("./eval_detail_model_mod.py", "../../motion_inbetweening/scripts/eval_detail_model_mod.py")
shutil.copyfile("./generatorLogic.py", "../../motion_inbetweening/scripts/generatorLogic.py")
shutil.copyfile("./json2bvhMotion.py", "../../motion_inbetweening/scripts/json2bvhMotion.py")
shutil.copyfile("./run_baseline_benchmark_mod.py", "../../motion_inbetweening/scripts/run_baseline_benchmark_mod.py")
shutil.copyfile("./baseStructure.bvh", "../../motion_inbetweening/scripts/baseStructure.bvh")
os.remove("../../motion_inbetweening/packages/motion_inbetween/benchmark.py")
shutil.copyfile("./benchmark.py", "../../motion_inbetweening/packages/motion_inbetween/benchmark.py")
shutil.copyfile("../configs/idle_ctx_model.json", "../../motion_inbetweening/configs/idle_ctx_model.json")
shutil.copyfile("../configs/idle_det_model.json", "../../motion_inbetweening/configs/idle_det_model.json")
print("Done.")