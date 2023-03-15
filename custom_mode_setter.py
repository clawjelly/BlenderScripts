# ------------------------------------
# Custom Mode Setter
# ------------------------------------
# Ver 0.2:
# - Cleaned up code
# - Fixed naming
# Ver 0.1:
# - First implementation
# ------------------------------------

import bpy

bl_info={
    "name" : "Custom Mode Setter",
    "author": "Oliver Reischl <clawjelly@gmail.net>",
    "version": (0, 2),
    "description" : "A custom submode setter, helps make blender behave like i want to",
    "blender": (2, 80, 1),
    "location": "",
    "warning": "",
    "wiki_url": "http://manuals.clawjelly.net/Blender/PersonalAddons",
    "category": "Generic"
}

class OP_custom_mode_setter(bpy.types.Operator):
    """A custom submode setter, helps make blender behave like i want to"""
    bl_idname = "olitools.custom_mode_setter"
    bl_label = "Custom Mode Setter"

    mode: bpy.props.IntProperty(
        name = 'Mode Number',
        default = 4
        )

    def custom_mode_setter(self, context, mode):
        obj = context.active_object
        # Is object a linked object?
        if obj.library != None:
            bpy.context.window_manager.popup_menu(
                lambda self, ctx: (self.layout.label(text="Can't edit linked objects.")) , 
                title="Warning", 
                icon='ERROR')
            return
        # print(f"Object {obj.name} in mode {obj.mode} set to Mode number: {mode}")
        if obj.type=='ARMATURE':
            print("Armature!")
            if mode==1:
                bpy.ops.object.mode_set(mode="EDIT")
            elif mode==2:
                bpy.ops.object.mode_set(mode="POSE")
            elif mode==4:
                bpy.ops.object.mode_set(mode="OBJECT")
        elif obj.type=='MESH':
            # In UV mode?
            if context.area.type=="IMAGE_EDITOR" and bpy.context.scene.tool_settings.use_uv_select_sync == False:
                print("Image Editor")
                if mode==1:
                    bpy.ops.uv.select_mode(type='VERTEX')
                if mode==2:
                    bpy.ops.uv.select_mode(type='EDGE')
                if mode==3:
                    bpy.ops.uv.select_mode(type='FACE')
                return
            ### still in 
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
        # elif obj.type=='CURVES':
        else:
            if mode==1:
                try:
                    bpy.ops.object.mode_set(mode="EDIT")
                except Exception as e:
                    pass
            else:
                bpy.ops.object.mode_set(mode="OBJECT")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        self.custom_mode_setter(context, self.mode)
        return {'FINISHED'}

blender_classes=[
    OP_custom_mode_setter,
]

def register():
    for blender_class in blender_classes:
        bpy.utils.register_class(blender_class)

def unregister():
    for blender_class in reversed(blender_classes):
        bpy.utils.unregister_class(blender_class)

if __name__ == "__main__":
    register()
