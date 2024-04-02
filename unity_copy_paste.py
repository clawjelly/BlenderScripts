bl_info = {
  "name": "Unity Copy/Paste Values",
  "description": "Copy/Paste functionality from/to Unity 3D Engine",
  "blender": (3, 0, 0),
  "version" : (1, 0, 1),
  "category": "Unity",
  "author": "Oliver Reischl"
}

import re
import bpy
from math import pi, radians
from mathutils import Vector, Quaternion, Matrix

def get_quaternions(obj):
    tempmode = obj.rotation_mode
    obj.rotation_mode = "QUATERNION"
    qrot = obj.rotation_quaternion
    obj.rotation_mode = tempmode  
    return qrot

def set_quaternions(obj, qrot):
    tempmode = obj.rotation_mode
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Quaternion(qrot)
    obj.rotation_mode = tempmode

class OLI_OT_copy_unity_location(bpy.types.Operator):
    """Copies position from active to clipboard"""
    bl_idname = "olitools.copy_unity_location"
    bl_label = "Copy Unity Location"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        # Vector3(5.99995255e-5,0.000982016325,0.000561989844)
        obj=context.active_object
        uPos=f"Vector3({obj.location.x*-1:5.8f},{obj.location.z:5.8f},{obj.location.y*-1:5.8f})"
        context.window_manager.clipboard = uPos
        return {'FINISHED'}

class OLI_OT_paste_unity_location(bpy.types.Operator):
    """Applies position from clipboard to active."""
    bl_idname = "olitools.paste_unity_location"
    bl_label = "Paste Unity Location"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        cp = context.window_manager.clipboard
        if "Vector3" in cp:
            posList=[float(i) for i in re.findall(r"[.0-9-e]{1,}", cp[7:])]
            print(posList)
            posVec=Vector([posList[0]*-1, posList[2]*-1, posList[1]])
            context.active_object.location=posVec
        return {'FINISHED'}

class OLI_OT_copy_unity_rotation(bpy.types.Operator):
    """Copies rotation as quaternions from active to clipboard"""
    bl_idname = "olitools.copy_unity_rotation"
    bl_label = "Copy Unity Rotation"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        unity_rot = Quaternion( (0, 0, 0.70710678118654752440084436210485, 0.70710678118654752440084436210485) )
        qRot = get_quaternions(context.active_object) @ unity_rot
        if context.active_object.type == "CAMERA":
            qRot @= Quaternion( (0, 0, 0, -1) )
        # uRot=f"Quaternion({qRot.x:5.9f},{qRot.z:5.9f},{qRot.y:5.9f},{-qRot.w:5.9f})" # normal
        uRot=f"Quaternion({-qRot.y:5.9f},{qRot.w:5.9f},{qRot.x:5.9f},{qRot.z:5.9f})" # vertify y -w x z
        context.window_manager.clipboard = uRot
        return {'FINISHED'}

class OLI_OT_paste_unity_rotation(bpy.types.Operator):
    """Applies rotation as quaternions from clipboard to active."""
    bl_idname = "olitools.paste_unity_rotation"
    bl_label = "Paste Unity Rotation"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        if "Quaternion" in context.window_manager.clipboard:
            posList=[float(i) for i in re.findall(r"[.0-9-e]{2,}", context.window_manager.clipboard)]
            print(posList)
            set_quaternions(context.active_object, [posList[3], posList[0], posList[1], posList[2]])
        return {'FINISHED'}


class OLI_PT_copy_paste_panel(bpy.types.Panel):
    bl_space_type="VIEW_3D"
    bl_region_type="UI"
    bl_category="Item"
    bl_label="Unity Copy/Paste"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def draw(self, context):
        box=self.layout.box()
        # row=box.row()
        split=box.split(align=True)
        split.operator("olitools.copy_unity_location")
        split.operator("olitools.paste_unity_location")

        split=box.split(align=True)
        split.operator("olitools.copy_unity_rotation")
        split.operator("olitools.paste_unity_rotation")

blender_classes=[
    OLI_OT_paste_unity_location,
    OLI_OT_copy_unity_location,
    OLI_OT_paste_unity_rotation,
    OLI_OT_copy_unity_rotation,
    OLI_PT_copy_paste_panel,
]

def register():
    for blender_class in blender_classes:
        bpy.utils.register_class(blender_class)

def unregister():
    for blender_class in blender_classes:
        bpy.utils.unregister_class(blender_class)

if __name__ == "__main__":
    register()