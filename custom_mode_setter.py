
# help from
# https://www.youtube.com/watch?v=uahfuypQQ04&feature=emb_logo

import bpy

bl_info={
    "name" : "object.custom_mode_setter",
    "author" : "clawjelly",
    "description" : "A custom submode setter, helps make blender behave like i want to",
    "blender": (2, 80, 1),
    "location": "",
    "warning": "",
    "wiki_url": "http://manuals.clawjelly.net/Blender/PersonalAddons",
    "category": "Generic"
}

def custom_mode_setter(context, mode):
    obj = context.active_object
    # print(context.view_layer.objects.active)
    print("OBJ: {} MODE: {} NUMBER: {}".format(obj, obj.mode, mode))
    if obj.type=='ARMATURE':
        print("Armature!")
        if mode==1:
            bpy.ops.object.mode_set(mode="EDIT")
        elif mode==2:
            bpy.ops.object.mode_set(mode="POSE")
        elif mode==4:
            bpy.ops.object.mode_set(mode="OBJECT")
    elif obj.type=='MESH':
        if mode==1:
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(type="VERT")
        elif mode==2:
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(type="EDGE")
        elif mode==3:
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(type="FACE")
        elif mode==4:
            bpy.ops.object.mode_set(mode="OBJECT")
    else:
        if mode==1:
            try:
                bpy.ops.object.mode_set(mode="EDIT")
            except Exception as e:
                pass
        else:
            bpy.ops.object.mode_set(mode="OBJECT")
                
# object.mode_set_with_submode
class CustomModeSetter(bpy.types.Operator):
    """A custom submode setter, helps make blender behave like i want to"""
    bl_idname = "object.custom_mode_setter"
    bl_label = "Custom Mode Setter"

    mode: bpy.props.IntProperty(
        name = 'Mode Number',
        default = 4
        )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        custom_mode_setter(context, self.mode)
        return {'FINISHED'}



def register():
    bpy.utils.register_class(CustomModeSetter)


def unregister():
    bpy.utils.unregister_class(CustomModeSetter)


if __name__ == "__main__":
    register()

    # test call
    # bpy.ops.object.custom_mode_setter()
