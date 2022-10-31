from pathlib import Path
import bpy

tex_keywords = {
    "ao": ["_ao", "ambientocclusion", "AmbientOcclusion", "ambientOcclusion"],
    "diffuse": ["_diffuse", "basemap", "albedo", "Albedo", "_alb"],
    "roughness": ["roughness", "_rgh", "Roughness"],
    "normal": ["_nrm", "_normal", "NormalMap", "normalmap"],
    "height": ["_height", "HeightMap", "heightmap"],
    "thumbnail": ["_render", "thumbnail", "Thumbnail"],
    "reflection": ["_reflection", "_ref", "Reflection"],
    "metal": ["_met", "metalness", "Metalness"],
    "emission": ["_emi", "Emission", "emissive"]
}

def get_texture_files(rpath):
    """ Searches the names of all files in a path for texture keywords
    Returns a dict of texture paths
    """
    tfiles = dict()
    for tfile in rpath.iterdir():
        if tfile.is_dir():
            continue
        if tfile.suffix!=".jpg" and tfile.suffix!=".png":
            continue
        for tkey, tids in tex_keywords.items():
            for tid in tids:
                if tid in tfile.stem:
                    tfiles[tkey]=tfile
                    break
    return tfiles

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

    if markasset:
        mat.asset_mark()
        if "thumbnail" in tfiles:
            with bpy.context.temp_override(id=mat):
                bpy.ops.ed.lib_id_load_custom_preview(filepath=str(tfiles["thumbnail"]))

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

    return mat

if __name__ == '__main__':
    wm = bpy.data.window_managers[0]

    # Put your filepath here:
    root = Path(r"H:\Files\Images\textures\Food")

    matPaths = list(p for p in root.iterdir() if p.is_dir())
    wm.progress_begin(0, len(matPaths))

    # tpath = Path(r"H:\Files\Images\textures\SciFi\Physical_3_Sci-Fi_4K\crt_display_screens_turned_on_28_99")
    # tid=1
    # if True:
    for tid, tpath in enumerate(matPaths):
        tfiles = get_texture_files(tpath)
        mat = generate_material(tpath.stem.replace("_", " "), tfiles, markasset=True, convertnormals=True)
        if mat.asset_data:
            # Add your tags here by replacing and duplicating this line as many times as needed
            mat.asset_data.tags.new("Metal")
        wm.progress_update(tid)

    wm.progress_end()