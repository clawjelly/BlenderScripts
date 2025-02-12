# ------------------------------------
# Custom Mode Setter
# ------------------------------------
# Ver 0.1:
# - Joining mode setter and delete
# ------------------------------------

import bpy

bl_info={
    "name" : "Oli Tools",
    "author": "Oliver Reischl <clawjelly@gmail.net>",
    "version": (0, 1),
    "description" : "Various little operators to ",
    "blender": (3, 5, 0),
    "location": "",
    "warning": "",
    "wiki_url": "http://manuals.clawjelly.net/Blender/PersonalAddons",
    "category": "Generic"
}

class OLI_OP_custom_mode_setter(bpy.types.Operator):
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

        # armatures
        if obj.type=='ARMATURE':
            print("Armature!")
            if mode==1:
                bpy.ops.object.mode_set(mode="EDIT")
            elif mode==2:
                bpy.ops.object.mode_set(mode="POSE")
            elif mode==4:
                bpy.ops.object.mode_set(mode="OBJECT")
            return

        # mesh sub object modes
        elif obj.type=='MESH':
            # In UV mode?
            if context.area.type=="IMAGE_EDITOR" and bpy.context.scene.tool_settings.use_uv_select_sync == False:
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
            return

        # default behaviour
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


class OLI_OT_delete_context(bpy.types.Operator):
    """A custom delete operator, mimicking the delete function in 3dsmax"""
    bl_idname = "olitools.delete_context"
    bl_label = "Delete/dissolve without dialog"

    @classmethod
    def poll(cls, context):
        isCorrect=  context.active_object is not None
        return isCorrect

    def execute(self, context):
        if context.mode=="EDIT_MESH":
            vertex, edge, face = context.scene.tool_settings.mesh_select_mode
            if vertex:
                bpy.ops.mesh.dissolve_verts()
            if edge:
                bpy.ops.mesh.dissolve_edges()
            if face:
                bpy.ops.mesh.delete(type='FACE')
            return {'FINISHED'}
        bpy.ops.object.delete()
        return {'FINISHED'}

class OLI_OT_select_full_hierarchy(bpy.types.Operator):
    """Selects the full hierarchy to the last child."""
    bl_idname = "olitools.select_full_hierarchy"
    bl_label = "Select full hierarchy"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        selected_objects = context.selected_objects
        obj_act = context.object

        if context.object not in selected_objects:
            selected_objects.append(context.object)

        while len(selected_objects)>0:
            obj = selected_objects.pop()
            selected_objects.extend([child for child in obj.children])
            obj.select_set(True)

        return {'FINISHED'}

class OLI_OT_increase_gizmo_size(bpy.types.Operator):
    """Increases the base size of all gimzos on the viewport"""
    bl_idname = "olitools.increase_gizmo_size"
    bl_label = "Increase Gizmo Size"

    def execute(self, context):
        sizes = [10, 20, 30, 50, 70, 100, 140, 200]
        current_size = context.preferences.view.gizmo_size
        for size in sizes:
            if size > current_size:
                context.preferences.view.gizmo_size = size
                break
        return {'FINISHED'}

class OLI_OT_decrease_gizmo_size(bpy.types.Operator):
    """Increases the base size of all gimzos on the viewport"""
    bl_idname = "olitools.decrease_gizmo_size"
    bl_label = "Decrease Gizmo Size"

    def execute(self, context):
        sizes = [200, 140, 100, 70, 50, 30, 20, 10]
        current_size = context.preferences.view.gizmo_size
        for size in sizes:
            if size < current_size:
                context.preferences.view.gizmo_size = size
                break
        return {'FINISHED'}


blender_classes=[
    OLI_OP_custom_mode_setter,
    OLI_OT_delete_context,
    OLI_OT_select_full_hierarchy,
    OLI_OT_increase_gizmo_size,
    OLI_OT_decrease_gizmo_size
]

def register():
    for blender_class in blender_classes:
        bpy.utils.register_class(blender_class)

def unregister():
    for blender_class in reversed(blender_classes):
        bpy.utils.unregister_class(blender_class)

if __name__ == "__main__":
    register()
