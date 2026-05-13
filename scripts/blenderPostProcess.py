import bpy
import math
import os

def postprocess(filename):
    # import the raw animation
    bvh_file_path = f"./bvh/{filename}.bvh"
    if(not os.path.exists(bvh_file_path)):
        print(f"{filename} does not exist")
        return
    bpy.ops.import_anim.bvh(filepath=bvh_file_path)

    # Get the active object
    obj = bpy.context.active_object

    if obj and obj.animation_data and obj.animation_data.action:
            fcurves = obj.animation_data.action.fcurves
            
            max_frame = 0
            for curve in fcurves:
                for keyframe in curve.keyframe_points:
                    max_frame = max(max_frame, keyframe.co[0])
    
    # create the jump indices
    jumps = [x*45 for x in range(1, int(max_frame)//45)]

    correctionCounter = 0
    for jump in jumps:
        if obj and obj.animation_data and obj.animation_data.action:
            fcurves = obj.animation_data.action.fcurves
            
            for curve in fcurves:
                axis = curve.array_index  # 0 = X, 1 = Y, 2 = Z
                axis_label = ["X", "Y", "Z"][axis]
                value1 = curve.keyframe_points[jump].co[1]
                lastValue1 = curve.keyframe_points[jump-1].co[1]
                nextValue1 = curve.keyframe_points[jump+1].co[1]
                offset1 = nextValue1 - ((value1 - lastValue1) + value1)

                for index, keyframe in enumerate(curve.keyframe_points):
                    if(curve.data_path != 'pose.bones["Hips"].location'):
                        if(index >= jump and index <= jump+45):
                            keyframe.co[1] += offset1
                            keyframe.co[1] -= offset1/45 * correctionCounter
                            correctionCounter +=1
                        if(index > jump+45):
                            correctionCounter = 0
                    else:
                        if(index >= jump):
                            keyframe.co[1] += offset1
        else:
            print("No animation data found on active object.")

    # Set the frame range to match the animation length
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = int(max_frame)
    # Apply corrective rotation (rotate -90 degrees on X axis)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.rotation_euler[0] = math.radians(-90)  # Rotate X by -90 degrees
    obj.rotation_euler[1] = math.radians(90)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    # Export the modified animation
    output_path = f"./bvh/{filename}_pp.bvh"
    bpy.ops.export_anim.bvh(filepath=output_path, root_transform_only = True)
    print(f"Exported processed animation to {output_path}")

for file in os.listdir("./bvh"):
    if file.endswith(".bvh") and not file.endswith("_pp.bvh") and "_ge" in file:
        postprocess(file.rstrip(".bvh"))