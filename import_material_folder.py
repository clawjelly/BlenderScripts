# -------------------------------------------------------------
# Material Folder Importer
# -------------------------------------------------------------
# Version 0.2
# -------------------------------------------------------------

bl_info = {
    "name": "Material Folder Importer",
    "author": "Oliver Reischl <clawjelly@gmail.net>",
    "version": (0, 3),
    "blender": (3, 00, 0),
    # "location": "View3D > Add > Mesh > New Object",
    "description": "Adds some more functionality to the Asset Browser",
    "doc_url": "https://github.com/clawjelly/BlenderScripts",
    "category": "Assets",
}

import json
import bpy
from pathlib import Path
from bpy_extras.io_utils import unique_name, ExportHelper, ImportHelper
from bpy.props import (
    StringProperty, 
    BoolProperty, 
    EnumProperty, 
    PointerProperty, 
    CollectionProperty, 
    IntProperty
    )
from bpy.types import PropertyGroup, AddonPreferences

file_types = [".jpg", ".png", ".tga"]

class ImportMaterialFolderPreferences(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    # ------- Ambient Occlusion -------------
    ao_keys: StringProperty( 
        name ="Ambient Occlusion",
        default = "_ao, _AO, ambientocclusion, AmbientOcclusion, ambientOcclusion"
        )

    # ------- Diffuse/Albedo -------------
    diffuse_keys: StringProperty( 
        name="Diffuse/Albedo",
        default="_diffuse, basemap, albedo, Albedo, _alb",
        )

    # ------- Roughness -------------
    roughness_keys: StringProperty( 
        name="Roughness",
        default="roughness, _rgh, Roughness",
        )

    # ------- Normal -------------
    normal_keys: StringProperty( 
        name="Normal",
        default="_nrm, _normal, NormalMap, normalmap",
        )

    # ------- Height -------------
    height_keys: StringProperty( 
        name="Height",
        default="_height, HeightMap, heightmap",
        )

    # ------- Thumbnail -------------
    thumbnail_keys: StringProperty( 
        name="Thumbnail",
        default="_render, thumbnail, Thumbnail",
        )

    # ------- Reflection -------------
    reflection_keys: StringProperty( 
        name="Reflection",
        default="_reflection, _ref, Reflection"
        )

    # ------- Metalness -------------
    metal_keys: StringProperty( 
        name="Metalness",
        default="_met, metalness, Metalness",
        )

    # ------- Emission -------------
    emission_keys: StringProperty( 
        name="Emission",
        default="_emi, Emission, emissive",
        )

    def draw(self, context):
        box = self.layout.box()
        box.label(text="Texture keywords, comma-seperated. The addon will look for all those.")
        box.prop(self, "ao_keys")
        box.prop(self, "diffuse_keys")
        box.prop(self, "roughness_keys")
        box.prop(self, "normal_keys")
        box.prop(self, "height_keys")
        box.prop(self, "thumbnail_keys")
        box.prop(self, "reflection_keys")
        box.prop(self, "metal_keys")
        box.prop(self, "emission_keys")

def get_node_by_id(mat, idname):
    for key, node in  mat.node_tree.nodes.items():
        if node.bl_idname == idname:
            return node
    return None

def generate_texture_nodes(mat, tpath, offset=(0,0)):
    """ Generates nodes for mapping, texture coordinates and image texture.
    Only generates mapping node if no mapping node exists. Otherwise recycles.
    """
    map_node = get_node_by_id(mat, "ShaderNodeMapping")
    if not map_node:
        # Texture Coordinates
        co_node=mat.node_tree.nodes.new("ShaderNodeTexCoord")
        co_node.location=(-1000+offset[0],0+offset[1])

        # Mapping node
        map_node=mat.node_tree.nodes.new("ShaderNodeMapping")
        map_node.location=(-750+offset[0],0+offset[1])
        mat.node_tree.links.new(co_node.outputs[2], map_node.inputs[0])

    # Texture
    tex_node=mat.node_tree.nodes.new("ShaderNodeTexImage")
    tex_node.location=(-500+offset[0],0+offset[1])
    mat.node_tree.links.new(map_node.outputs[0], tex_node.inputs[0])
    img=bpy.data.images.load(str(tpath))
    tex_node.image=img

    return tex_node


def generate_material(matName, tfiles, markasset=False, convertnormals=True):
    """Generates a material from a list of texture file paths.

    markasset: Marks the material as a blender asset, so it will show up in the assetdb
    convertnormals: Adds nodes to convert from DirectX- to OpenGL-style normal maps
    """

    mat=bpy.data.materials.new(matName)
    mat.cycles.displacement_method = 'BOTH'
    mat.use_nodes=True
    shader_node=mat.node_tree.nodes["Principled BSDF"]
    output_node=get_node_by_id(mat, "ShaderNodeOutputMaterial")
    if not output_node:
        assert("No output node?!!")

    # Diffuse
    if "diffuse" in tfiles:
        diftex = generate_texture_nodes(mat, tfiles["diffuse"], offset=(-500,900))
        mat.node_tree.links.new(diftex.outputs[0], shader_node.inputs[0])

    # AO
    if "ao" in tfiles:
        aoTex = generate_texture_nodes(mat, tfiles["ao"], offset=(-500,1200))
        aoTex.image.colorspace_settings.name = 'Non-Color'

    # AO
    if "reflection" in tfiles:
        refTex = generate_texture_nodes(mat, tfiles["reflection"], offset=(-500,1500))
        refTex.image.colorspace_settings.name = 'Non-Color'

    # Roughness
    if "roughness" in tfiles:
        roughtex = generate_texture_nodes(mat, tfiles["roughness"], offset=(-500,300))
        roughtex.image.colorspace_settings.name = 'Non-Color'
        mat.node_tree.links.new(roughtex.outputs[0], shader_node.inputs[9])

    # Metalness
    if "metal" in tfiles:
        metalTex = generate_texture_nodes(mat, tfiles["metal"], offset=(-500,600))
        metalTex.image.colorspace_settings.name = 'Non-Color'
        mat.node_tree.links.new(metalTex.outputs[0], shader_node.inputs[6])

    # Emission
    if "emission" in tfiles:
        emiTex = generate_texture_nodes(mat, tfiles["emission"], offset=(-500,0))
        emiTex.image.colorspace_settings.name = 'Non-Color'
        mat.node_tree.links.new(emiTex.outputs[0], shader_node.inputs[19])

    # Normalmap
    if "normal" in tfiles:
        normaltex = generate_texture_nodes(mat, tfiles["normal"], offset=(-500,-300))
        normaltex.image.colorspace_settings.name = 'Non-Color'
        normalnode = mat.node_tree.nodes.new("ShaderNodeNormalMap")
        normalnode.location=(-200, -400)
        # normal fixer
        if convertnormals:
            seperatenode = mat.node_tree.nodes.new("ShaderNodeSeparateColor")
            seperatenode.location=(-710, -400)
            subnode = mat.node_tree.nodes.new("ShaderNodeMath")
            subnode.operation = 'SUBTRACT'
            subnode.inputs[0].default_value = 1
            subnode.location=(-540, -400)
            combinenode = mat.node_tree.nodes.new("ShaderNodeCombineColor")
            combinenode.location=(-370, -400)
            # connections
            mat.node_tree.links.new(normaltex.outputs[0], seperatenode.inputs[0])
            mat.node_tree.links.new(seperatenode.outputs[1], subnode.inputs[1])
            mat.node_tree.links.new(subnode.outputs[0], combinenode.inputs[1])
            mat.node_tree.links.new(seperatenode.outputs[0], combinenode.inputs[0])
            mat.node_tree.links.new(seperatenode.outputs[2], combinenode.inputs[2])
            mat.node_tree.links.new(combinenode.outputs[0], normalnode.inputs[1])
        else:
            mat.node_tree.links.new(normaltex.outputs[0], normalnode.inputs[1])
            
        mat.node_tree.links.new(normalnode.outputs[0], shader_node.inputs[22])

    # Height
    if "height" in tfiles:
        heightTex = generate_texture_nodes(mat, tfiles["height"], offset=(-500,-600))
        heightTex.image.colorspace_settings.name = 'Non-Color'
        dispNode = mat.node_tree.nodes.new("ShaderNodeDisplacement")
        dispNode.location=(120, -500)
        dispNode.inputs[2].default_value = 0.03
        mat.node_tree.links.new(heightTex.outputs[0], dispNode.inputs[0])
        mat.node_tree.links.new(dispNode.outputs[0], output_node.inputs[2])

    if markasset:
        mat.asset_mark()
        if "thumbnail" in tfiles:
            with bpy.context.temp_override(id=mat):
                bpy.ops.ed.lib_id_load_custom_preview(filepath=str(tfiles["thumbnail"]))
        else:
            with bpy.context.temp_override(id=mat):
                bpy.ops.ed.lib_id_generate_preview()

    return mat

class OLI_PG_material_importer_settings(PropertyGroup):

    path : StringProperty(
        name="Folder",
        description="Path to root material directory",
        default="",
        maxlen=1024,
        subtype='DIR_PATH')

    mark_asset: BoolProperty(
        default=True, 
        description="Create a material asset"
        )

    convert_from_directx: BoolProperty(
        default=True,
        description="Add nodes to correct DirectX style normalmaps."
        )

    tag1 : StringProperty(
        name="Adds an asset tag",
        default=""
        )

    tag2 : StringProperty(
        name="Adds an asset tag",
        default=""
        )

    tag3 : StringProperty(
        name="Adds an asset tag",
        default=""
        )

class OLI_OT_import_material_folder(bpy.types.Operator):
    """ Import a whole folder with a subfolder each
    for one material. Tries to assign the textures to
    their right slot according to their filenames."""
    bl_idname = "olitools.import_material_folder"
    bl_label = "Import Folder"

    filepath: StringProperty()
    filename:  StringProperty()
    directory:  StringProperty()

    # def __init__(self):
    #     pass

    def get_texture_files(self, context, rpath):
        """ Searches the names of all files in a path for texture keywords
        Returns a dict of texture paths
        """

        # build keyword dict
        preferences = context.preferences
        addon_prefs = preferences.addons[__name__].preferences
        tex_keywords = dict()
        tex_keywords["ao"]          =[key.strip() for key in addon_prefs.ao_keys.split(",")]
        tex_keywords["diffuse"]     =[key.strip() for key in addon_prefs.diffuse_keys.split(",")]
        tex_keywords["reflection"]  =[key.strip() for key in addon_prefs.reflection_keys.split(",")]
        tex_keywords["roughness"]   =[key.strip() for key in addon_prefs.roughness_keys.split(",")]
        tex_keywords["metal"]       =[key.strip() for key in addon_prefs.metal_keys.split(",")]
        tex_keywords["emission"]    =[key.strip() for key in addon_prefs.emission_keys.split(",")]
        tex_keywords["normal"]      =[key.strip() for key in addon_prefs.normal_keys.split(",")]
        tex_keywords["height"]      =[key.strip() for key in addon_prefs.height_keys.split(",")]
        tex_keywords["render"]      =[key.strip() for key in addon_prefs.thumbnail_keys.split(",")]

        # build file dict
        tfiles = dict()
        for tfile in rpath.iterdir():
            if tfile.is_dir():
                continue
            if tfile.suffix not in file_types:
                continue
            for tkey, tids in tex_keywords.items():
                # print(f"Tex Type {tkey} has {len(tids)} keywords")
                for tid in tids:
                    if tid in tfile.stem:
                        tfiles[tkey]=tfile
                        break
        return tfiles    

    def invoke(self, context, _event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}        

    def execute(self, context):

        # first get directory
        # root = Path(context.scene.material_importer_settings.path)
        root = Path(self.directory)
        print(root)
        if not root.is_dir():
            bpy.context.window_manager.popup_menu(
                lambda self, ctx: (self.layout.label(text="Not a folder.")) , 
                title="Warning", 
                icon='ERROR')
            return {'CANCELLED'}

        wm = context.window_manager

        matPaths = list(p for p in root.iterdir() if p.is_dir())
        wm.progress_begin(0, len(matPaths))

        for tid, tpath in enumerate(matPaths):
            tfiles = self.get_texture_files(context, tpath)
            mark_asset = context.scene.material_importer_settings.mark_asset
            convert = context.scene.material_importer_settings.convert_from_directx
            mat = generate_material(tpath.stem.replace("_", " "), tfiles, markasset=mark_asset, convertnormals=convert)
            if mat.asset_data:
                if context.scene.material_importer_settings.tag1!="":
                    mat.asset_data.tags.new(context.scene.material_importer_settings.tag1)
                if context.scene.material_importer_settings.tag2!="":
                    mat.asset_data.tags.new(context.scene.material_importer_settings.tag2)
                if context.scene.material_importer_settings.tag3!="":
                    mat.asset_data.tags.new(context.scene.material_importer_settings.tag3)
            wm.progress_update(tid)

        wm.progress_end()
        return {'FINISHED'}

class OLI_PT_import_material_folder(bpy.types.Panel):
    # bl_space_type="VIEW_3D"
    # bl_region_type="UI"
    # bl_category="Tool"
    bl_space_type="FILE_BROWSER"
    bl_region_type="TOOL_PROPS"
    bl_category="assets"    
    bl_label="Material Importer"

    @classmethod
    def poll(cls, context):
        return context.area.ui_type=="ASSETS"

    def draw(self, context):
        box = self.layout.box()
        box.prop(context.scene.material_importer_settings, "mark_asset", text="Mark as asset")
        box.prop(context.scene.material_importer_settings, "convert_from_directx", text="Add DX Conversion")

        col = box.column(align=True)
        col.label(text="Tags")
        col.prop(context.scene.material_importer_settings, "tag1", text="1")
        col.prop(context.scene.material_importer_settings, "tag2", text="2")
        col.prop(context.scene.material_importer_settings, "tag3", text="3")

        self.layout.operator("olitools.import_material_folder", text="Import Materials")

blender_classes=[
    ImportMaterialFolderPreferences,
    OLI_PG_material_importer_settings,
    OLI_OT_import_material_folder,
    OLI_PT_import_material_folder
]

def register():
    for blender_class in blender_classes:
        bpy.utils.register_class(blender_class)
    bpy.types.Scene.material_importer_settings = PointerProperty(type=OLI_PG_material_importer_settings)

def unregister():
    del bpy.types.Scene.material_importer_settings
    for blender_class in blender_classes:
        bpy.utils.unregister_class(blender_class)

if __name__ == "__main__":
    print("------- Unregister...")
    try:
        unregister()
    except Exception as e:
        print("Excerption!")
        print(e)
    print("------- Register...")
    register()
    print("------- Done!")