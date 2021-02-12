import bpy

bl_info={
    "name" : "Delete Mesh Context",
    "author" : "clawjelly",
    "description" : "Deletes depending on context vertices, edges or faces. Without a dialog.",
    "blender": (2, 80, 1),
    "location": "",
    "warning": "",
    "wiki_url": "http://manuals.clawjelly.net/Blender/PersonalAddons",    
    "category": "Mesh"
}


def main(context):

    # if context.mode=="OBJECT":
    #     bpy.ops.object.delete()
    #     return

    if context.mode=="EDIT_MESH":
        # print("Sub Mode Enabled!")
        vertex, edge, face = context.scene.tool_settings.mesh_select_mode
        # print("V: {} - E: {} - F: {}".format(vertex, edge, face))
        if vertex:
            # print("Verts deleted!")
            # bpy.ops.mesh.delete(type='VERT')
            bpy.ops.mesh.dissolve_verts()
        if edge:
            # print("Edges deleted!")
            # bpy.ops.mesh.delete(type='EDGE')
            bpy.ops.mesh.dissolve_edges()
        if face:
            # print("Faces deleted!")
            bpy.ops.mesh.delete(type='FACE')
        return

    bpy.ops.object.delete()
    return

class DeleteContextOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "mesh.delete_context"
    bl_label = "Delete Context Operator"

    @classmethod
    def poll(cls, context):
        isCorrect=  context.active_object is not None
        return isCorrect

    def execute(self, context):
        main(context)
        return {'FINISHED'}


def register():
    bpy.utils.register_class(DeleteContextOperator)


def unregister():
    bpy.utils.unregister_class(DeleteContextOperator)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.mesh.delete_context()
