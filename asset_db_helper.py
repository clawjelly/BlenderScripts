
bl_info = {
    "name": "AssetDB Helper",
    "author": "Oliver Reischl <clawjelly@gmail.net>",
    "version": (1, 0),
    "blender": (3, 00, 0),
    # "location": "View3D > Add > Mesh > New Object",
    "description": "Adds some more functionality to the Asset Browser",
    "category": "Assets",
}

import bpy
from bpy_extras.asset_utils import (
    SpaceAssetInfo,
)

class OLI_OT_test_asset_db(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "assets.test_asset_db"
    bl_label = "Asset DB test"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        # isDef = SpaceAssetInfo.is_asset_browser_poll(context)
        # space_data = context.space_data
        # print(dir(space_data))
        # params = space_data.params
        # print(dir(params))
        asset=SpaceAssetInfo.get_active_asset(bpy.context)
        print(context.asset_file_handle)

        return {'FINISHED'}

class OLI_OT_add_active_tags_to_all(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "assets.add_active_tags_to_all"
    bl_label = "Copy Tags of Active to All"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        asset = SpaceAssetInfo.get_active_asset(context)
        print(f"{asset.tags}")
        assets = [obj for obj in context.selectable_objects if obj.asset_data != None]
        print(f"Object Assets: {len(assets)}")
        for obj in assets:
            for tag in asset.tags:
                if tag.name in obj.asset_data.tags:
                    print(f"Found {tag} in {obj.name}")
                else:
                    obj.asset_data.tags.new(tag.name)
        mats = [mat for mat in bpy.data.materials if mat.asset_data != None]
        print(f"Material Assets: {len(assets)}")
        for mat in mats:
            for tag in asset.tags:
                if tag.name in mat.asset_data.tags:
                    print(f"Found {tag} in {mat.name}")
                else:
                    mat.asset_data.tags.new(tag.name)        
        bpy.ops.ed.undo_push()
        return {'FINISHED'}

class OLI_PT_asset_db_helper(bpy.types.Panel):
    bl_space_type="FILE_BROWSER"
    bl_region_type="TOOL_PROPS"
    bl_category="assets"
    bl_label="AssetDB Helper"

    @classmethod
    def poll(cls, context):
        return (SpaceAssetInfo.get_active_asset(context) is not None)

    def draw(self, context):
        layout = self.layout
        layout.operator("assets.test_asset_db")
        layout.operator("assets.add_active_tags_to_all")
        layout.operator("asset.open_containing_blend_file")
        pass

blender_classes=[
    OLI_OT_test_asset_db,
    OLI_OT_add_active_tags_to_all,
    OLI_PT_asset_db_helper
]

def register():
    for blender_class in blender_classes:
        bpy.utils.register_class(blender_class)

def unregister():
    for blender_class in blender_classes:
        try:
            bpy.utils.unregister_class(blender_class)
        except:
            pass

if __name__ == "__main__":
    unregister()
    register()