# -------------------------------------------------------------
# Rapid Gamedev Toolchain
# -------------------------------------------------------------
# Version 0.4:
# - Supporting GLTF file format
# - Export all objects
# Version 0.3:
# - Bugfix: Armatures
# Version 0.2:
# - Change to RGT
# -------------------------------------------------------------

bl_info = {
	"name": "Rapid Gamedev Toolchain",
	"author": "Oliver Reischl <clawjelly@gmail.net>",
	"version": (0, 2),
	"blender": (3, 00, 0),
	"description": "Helps to setup game objects for export.",
	"category": "Assets",
}

# standard imports
import json, subprocess, re
from pathlib import Path
from abc import ABC, abstractmethod
from tempfile import gettempdir

# blender
import bpy
from bpy.path import abspath, relpath
from bpy.types import PropertyGroup, AddonPreferences
from bpy_extras.io_utils import ExportHelper
from bpy.props import (
	StringProperty, 
	BoolProperty, 
	EnumProperty, 
	PointerProperty, 
	CollectionProperty, 
	IntProperty
	)

# -----------------------------------------------------------------------
# Base Functions
# -----------------------------------------------------------------------

exp_types = ["MESH", "ARMATURE", "EMPTY"]

def select(*objs):
	bpy.ops.object.select_all(action='DESELECT')
	bpy.context.view_layer.objects.active = objs[0]
	for obj in objs:
		print(f"Selecting {obj.name}")
		obj.select_set(True)

def get_hierarchy(*objs):
	newobjs=[]    
	testobjs=list(objs)
	while testobjs:
		obj=testobjs.pop()
		testobjs.extend(obj.children)
		newobjs.append(obj)
	return newobjs

def clean_name(namestring):
	rx = re.compile('\W+')
	return rx.sub(' ', namestring).strip()

def has_armature(obj):
    for mod in obj.modifiers:
        if mod.type=="ARMATURE":
            return True
    return False

def update_export_path_suffix():
	"""Fixes all objects export path suffixes."""
	global export_format
	for obj in bpy.context.scene.objects:
		if obj.toolchain_settings.export_path=="":
			continue
		parts = obj.toolchain_settings.export_path.split(".")
		obj.toolchain_settings.export_path = parts[0] + export_format.current.suffix

# -----------------------------------------------------------------------
# Format Abstract class
# -----------------------------------------------------------------------

class File_format(ABC):

	@abstractmethod
	def get_default_settings(self):
		return {}

	@abstractmethod
	def save_settings(self, settings = None):
		pass

	@abstractmethod
	def load_settings(self):
		pass

	@abstractmethod
	def check_for_export(self, obj):
		return ""

	@abstractmethod
	def export(self, filepath, object_settings):
		pass

# -----------------------------------------------------------------------
# FBX Functions
# -----------------------------------------------------------------------

class FBX_file_format(File_format):

	def __init__(self, *args, **kwargs ):
		super().__init__( *args, **kwargs )
		self.suffix = ".fbx"
		self.id = "FBX"

	def get_default_settings(self):
		return {
			"use_selection" : True,
			"use_visible" : False,
			"use_active_collection" : False,
			"global_scale" : 1.0,
			"apply_unit_scale" : True,
			"apply_scale_options" : 'FBX_SCALE_UNITS',
			"use_space_transform" : True,
			"bake_space_transform" : True,
			"object_types" : {'OTHER', 'CAMERA', 'ARMATURE', 'LIGHT', 'EMPTY', 'MESH'},
			"use_mesh_modifiers" : True,
			"use_mesh_modifiers_render" : True,
			"mesh_smooth_type" : 'OFF',
			"use_subsurf" : False,
			"use_mesh_edges" : False,
			"use_tspace" : False,
			"use_triangles" : False,
			"use_custom_props" : False,
			"add_leaf_bones" : True,
			"primary_bone_axis" : 'Y',
			"secondary_bone_axis" : 'X',
			"use_armature_deform_only" : False,
			"armature_nodetype" : 'NULL',
			"bake_anim" : True,
			"bake_anim_use_all_bones" : True,
			"bake_anim_use_nla_strips" : True,
			"bake_anim_use_all_actions" : True,
			"bake_anim_force_startend_keying" : True,
			"bake_anim_step" : 1.0,
			"bake_anim_simplify_factor" : 1.0,
			"path_mode" : 'AUTO',
			"embed_textures" : False,
			"batch_mode" : 'OFF',
			"use_batch_own_dir" : True,
			"axis_forward" : 'Z',
			"axis_up" : 'Y'
		}

	def save_settings(self, settings = None):
		"""Saves the fbx export settings. If none are given, it saves default settings."""
		global export_format
		cPath=Path(bpy.utils.resource_path(type="USER")) / "config"

		if settings == None:
			settings = dict()
			settings["default"] = export_format.current.get_default_settings()
			settings["default"]["object_types"]=list(settings["default"]["object_types"])

		with open(cPath / "ot_fbx_settings.json", "w") as jsonfile:
			json.dump(settings, jsonfile, indent=2)

	def load_settings(self):
		"""Loads the fbx export settings. If none are found, it creates default settings"""
		global export_format
		cPath=Path(bpy.utils.resource_path(type="USER")) / "config" / "ot_fbx_settings.json"

		if not cPath.exists():
			export_format.current.save_settings() # save defaults

		with open(cPath) as jsonfile:
			settings = json.load(jsonfile)
			for key, item in settings.items():
				settings[key]["object_types"]=set(settings[key]["object_types"])

		return settings

	def check_for_export(self, obj):
		if obj.type not in exp_types:
			return f"- {obj.name} needs to be exportable (e. g. a mesh, armature, empty...)."
		if hasattr(obj.data, "shape_keys"):
			if len(obj.modifiers)==1:
				if obj.modifiers[0].type=="ARMATURE":
					return ""
				else:
					return f"- {obj.name} has shape keys and modifiers, hence shape keys cannot be exported."
			if len(obj.modifiers)>1:
				return f"- {obj.name} has shape keys and modifiers, hence shape keys cannot be exported."
		return ""

	def export(self, filepath, object_settings):
		bpy.ops.export_scene.fbx(filepath=filepath, **object_settings)

# -----------------------------------------------------------------------
# GLTF Functions
# -----------------------------------------------------------------------

class GLTF_file_format(File_format):

	def __init__(self, *args, **kwargs ):
		super().__init__( *args, **kwargs )
		self.suffix = ".gltf"
		self.id = "GLTF"

	def get_default_settings(self):
		return {
			"export_import_convert_lighting_mode" : 'SPEC',
			"gltf_export_id" : '',
			"export_format" : 'GLTF_SEPARATE',
			"export_copyright" : '',
			"export_image_format" : 'AUTO',
			"export_image_add_webp" : False,
			"export_image_webp_fallback" : False,
			"export_texture_dir" : '',
			"export_jpeg_quality" : 75,
			"export_image_quality" : 75,
			"export_keep_originals" : True,
			"export_texcoords" : True,
			"export_normals" : True,
			"export_draco_mesh_compression_enable" : False,
			"export_draco_mesh_compression_level" : 6,
			"export_draco_position_quantization" : 14,
			"export_draco_normal_quantization" : 10,
			"export_draco_texcoord_quantization" : 12,
			"export_draco_color_quantization" : 10,
			"export_draco_generic_quantization" : 12,
			"export_tangents" : False,
			"export_materials" : 'EXPORT',
			"export_colors" : True,
			"export_attributes" : False,
			"use_mesh_edges" : False,
			"use_mesh_vertices" : False,
			"export_cameras" : False,
			"use_selection" : True,
			"use_visible" : False,
			"use_renderable" : False,
			"use_active_collection_with_nested" : True,
			"use_active_collection" : False,
			"use_active_scene" : False,
			"export_extras" : False,
			"export_yup" : True,
			"export_apply" : False,
			"export_animations" : True,
			"export_frame_range" : False,
			"export_frame_step" : 1,
			"export_force_sampling" : True,
			"export_animation_mode" : 'ACTIONS',
			"export_nla_strips_merged_animation_name" : 'Animation',
			"export_def_bones" : False,
			"export_hierarchy_flatten_bones" : False,
			"export_optimize_animation_size" : True,
			"export_optimize_animation_keep_anim_armature" : True,
			"export_optimize_animation_keep_anim_object" : False,
			"export_negative_frame" : 'SLIDE',
			"export_anim_slide_to_zero" : False,
			"export_bake_animation" : False,
			"export_anim_single_armature" : True,
			"export_reset_pose_bones" : True,
			"export_current_frame" : False,
			"export_rest_position_armature" : True,
			"export_anim_scene_split_object" : True,
			"export_skins" : True,
			"export_influence_nb" : 4,
			"export_all_influences" : False,
			"export_morph" : True,
			"export_morph_normal" : True,
			"export_morph_tangent" : False,
			"export_morph_animation" : True,
			"export_morph_reset_sk_data" : True,
			"export_lights" : False,
			"export_try_sparse_sk" : True,
			"export_try_omit_sparse_sk" : False,
			"export_gpu_instances" : False,
			"export_nla_strips" : True,
			"export_original_specular" : False,
			"will_save_settings" : False
		}

	def save_settings(self, settings = None):
		"""Saves the fbx export settings. If none are given, it saves default settings."""
		global export_format
		cPath=Path(bpy.utils.resource_path(type="USER")) / "config"

		if settings == None:
			settings = dict()
			settings["default"] = export_format.current.get_default_settings()

		with open(cPath / "ot_gltf_settings.json", "w") as jsonfile:
			json.dump(settings, jsonfile, indent=2)

	def load_settings(self):
		"""Loads the fbx export settings. If none are found, it creates default settings"""
		global export_format
		cPath=Path(bpy.utils.resource_path(type="USER")) / "config" / "ot_gltf_settings.json"

		if not cPath.exists():
			export_format.current.save_settings() # save defaults

		with open(cPath) as jsonfile:
			settings = json.load(jsonfile)

		return settings

	def check_for_export(self, obj):
		# TODO: Need to check for issues.
		return ""

	def export(self, filepath, object_settings):
		bpy.ops.export_scene.gltf(filepath=filepath, **object_settings)

# -----------------------------------------------------------------------
# Global File Format Settings
# -----------------------------------------------------------------------

class ExportFormatManager:

	def __init__(self, *args, **kwargs ):
		self.existing_formats = dict()
		self.existing_formats["FBX"] = FBX_file_format()
		self.existing_formats["GLTF"] = GLTF_file_format()

	def get_current_export_format(self):
		return self.existing_formats[bpy.context.scene.toolchain_settings.export_format]

	current = property(get_current_export_format)

export_format = ExportFormatManager()

# -----------------------------------------------------------------------
# Addon Settings
# -----------------------------------------------------------------------

class OLI_AP_rapid_gamedev_toolchain_settings(AddonPreferences):
	# this must match the add-on name, use '__package__'
	# when defining this in a submodule of a python package.
	bl_idname = "rapid_gamedev_toolchain" # __name__

	painter_exe: bpy.props.StringProperty(
		name="Painter EXE",
		description="Substance Painter Executeable Path",
		subtype="FILE_PATH",
		default="",
		maxlen=0
	)

	designer_exe: bpy.props.StringProperty(
		name="Designer EXE",
		description="Affinty Designer Executeable Path",
		subtype="FILE_PATH",
		default="",
		maxlen=0
	)

	def draw(self, context):
		box = self.layout.box()
		box.prop(self, "painter_exe", text="Painter EXE")
		box.prop(self, "designer_exe", text="Designer EXE")

# -----------------------------------------------------------------------
# Scene Settings
# -----------------------------------------------------------------------

class OLI_PG_export_directory_settings(PropertyGroup):
	
	def update_project_path(self, context):
		value = context.scene.toolchain_settings.project_path
		# self["project_path"] = str(Path(abspath(value)).resolve())
		self["project_path"] = abspath(value)

	def update_format(self, context):
		global export_format
		print(f"Selecting {context.scene.toolchain_settings.export_format} format with {export_format.current.suffix} ending.")
		# fix all objects
		update_export_path_suffix()

	project_path: bpy.props.StringProperty(
		name="Export Path",
		description="The filepath of the exports.",
		default="",
		subtype="NONE",
		maxlen=0,
		update = update_project_path
	)

	export_format: bpy.props.EnumProperty(
		name = "Export Format",
		description = "The final export format. Depends on the used engine.",
		items = (("FBX", "FBX File", ""), ("GLTF", "GLTF File", "")),
		update = update_format,
		default = "FBX"
	)

	map_export_directory: bpy.props.StringProperty(
		name="Texture Map Export Directory",
		description="This is where painter should export maps to. If empty, none will be specified.",
		default="",
		subtype="DIR_PATH",
		maxlen=0
	)

	uv_export_directory: bpy.props.StringProperty(
		name="UV Template Export Directory",
		description="This is where the UV template will be saved.",
		default="",
		subtype="DIR_PATH",
		maxlen=0
	)

	uv_resolution: bpy.props.IntProperty(
		name="UV resolution",
		default=2048,
		min=0, max=4096,
		description="This is needed for export, even though we're exporting shapes."
	)

# -----------------------------------------------------------------------
# Object Settings
# -----------------------------------------------------------------------

class OLI_PG_export_object_settings(PropertyGroup):

	# Issues with PropertyGroup and setters?! No idea.
	def update_obj_export_path(self, context):
		global export_format
		if self['export_path'] =="":
			return
		obj_path = Path(self['export_path'])
		# check for relative path to project
		if context.scene.toolchain_settings.project_path!="":
			prj_path = Path(context.scene.toolchain_settings.project_path)
			if obj_path.is_relative_to(prj_path):
				obj_path = obj_path.relative_to(prj_path)
		# fix suffix
		# if obj_path.suffix!=export_format.current.suffix:
		# 	obj_path = obj_path.with_suffix(export_format.current.suffix)
		self["export_path"] = str(obj_path)

	def settings_callback(self, context):
		global export_format
		items = [(key, key, "") for key, item in export_format.current.load_settings().items()]
		return items

	export_path: bpy.props.StringProperty(
		name="Export Path",
		description="The export path relative to the project to directory.",
		default="",
		# subtype="FILE_PATH",
		update = update_obj_export_path,
		subtype="NONE",
		maxlen=0
	)

	export_settings: bpy.props.EnumProperty(
		name="Export Settings",
		items=settings_callback,
		# items = [ ( "default", "default", "The standard export settings.") ],
		description="The export settings to be used to export.",
		default=None, 
		#options={},
		override=set(),
		update=None,
		get=None,
		set=None
	)

	center: bpy.props.BoolProperty(
		name="Center before exports",
		default=True,
		description="For export set the object temporary to world center."
	)

# -----------------------------------------------------------------------
# File Open Dialog Operators
# -----------------------------------------------------------------------

class OLI_OT_select_project_path(bpy.types.Operator):
	"""Select Project Path"""
	bl_idname = "olitools.select_project_path"
	bl_label = "Select Project Path"

	filter_glob: StringProperty(
		default="*.*",
		options={'HIDDEN'},
		maxlen=255,  # Max internal buffer length, longer would be clamped.
	)

	filepath: StringProperty()
	filename:  StringProperty()
	directory:  StringProperty()

	@classmethod
	def poll(cls, context):
		if context.active_object==None:
			return False
		return True

	def invoke(self, context, _event):
		"""This is called before any window opens."""
		if context.scene.toolchain_settings.project_path=="":
			self.filepath = context.scene.toolchain_settings.project_path
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

	def execute(self, context):
		"""This is called after the window opened."""
		context.scene.toolchain_settings.project_path = abspath(self.filepath)
		return {'FINISHED'}

class OLI_OT_object_export_file_path_window(bpy.types.Operator):
	"""Set Export Path for the Object"""
	bl_idname = "olitools.object_export_file_path_window"
	bl_label = "Set Export Path"

	filter_glob: StringProperty(
		default = "*.*",
		options = {'HIDDEN'},
		maxlen = 255,  # Max internal buffer length, longer would be clamped.
	)

	filepath:   StringProperty()
	filename:   StringProperty()
	directory:  StringProperty()

	@classmethod
	def poll(cls, context):
		if context.scene.toolchain_settings.project_path=="":
			return False
		if context.active_object==None:
			return False
		return True

	def invoke(self, context, _event):
		"""This is called before any window opens."""
		global export_format
		# self.filter_glob["default"] = current_export_format.suffix
		if context.active_object.toolchain_settings.export_path=="":
			self.filepath = context.scene.toolchain_settings.project_path + "\\" + context.active_object.name + export_format.current.suffix
		else:
			self.filepath = context.scene.toolchain_settings.project_path + "\\" + context.active_object.toolchain_settings.export_path
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

	def execute(self, context):
		"""This is called after the window opened."""
		global export_format
		print(f"Filepath: {self.filepath}, current suffix: {export_format.current.suffix}")

		parts = self.filepath.split(".")
		context.active_object.toolchain_settings.export_path = abspath(parts[0] + export_format.current.suffix)

		return {'FINISHED'}

# -----------------------------------------------------------------------
# Export
# -----------------------------------------------------------------------

class OLI_OT_export_to_directory(bpy.types.Operator):
	"""Exports the object to an FBX inside the stored directory."""
	bl_idname = "export.to_directory"
	bl_label = "Exports object to a set filepath with defined settings."

	@classmethod
	def poll(cls, context):
		if context.scene.toolchain_settings.project_path=="":
			return False
		if context.active_object==None:
			return False
		if context.active_object.toolchain_settings.export_path=="":
			return False
		if len(context.selected_objects)!=1:
			return False
		return True

	def execute(self, context):
		global export_format
		settings = export_format.current.load_settings()
		project_path = Path(context.scene.toolchain_settings.project_path)
		object_path = Path(context.active_object.toolchain_settings.export_path)
		if object_path.suffix!=export_format.current.suffix:
			object_path=object_path.with_suffix(export_format.current.suffix)
		object_settings = context.active_object.toolchain_settings.export_settings
		if object_settings not in settings:
			bpy.context.window_manager.popup_menu(
				lambda self, ctx: (self.layout.label(text=f"Settings '{object_settings}' not found. Reverting to default settings.")) , 
				title="Warning", 
				icon='ERROR')
			# return {"CANCELLED"}
			object_settings = "default"

		center = context.active_object.toolchain_settings.center

		# We want to export the full hierarchy. No idea why that isn't even considered in the exporter itself.
		obj = context.active_object

		if has_armature(obj) and obj.parent and obj.parent.type=="ARMATURE":
			select(*get_hierarchy(obj), obj.parent)
		else:
			select(*get_hierarchy(obj))

		# Check for any export issues.
		issues = []
		for cobj in context.selected_objects:
			msg = export_format.current.check_for_export(cobj)
			if msg!="":
				issues+=msg
		if len(issues)!=0:
			bpy.context.window_manager.popup_menu(
				lambda self, ctx: (self.layout.label(text="\n".join(issues))) , 
				title="Export unsuccessful because following problems were found:", 
				icon='ERROR')
			return {"CANCELLED"}

		if center:
			ox, oy, oz = obj.location
			obj.location = 0, 0, 0		

		res = export_format.current.export(str(project_path / object_path), settings[object_settings])
		try:
			pass
			# bpy.ops.export_scene.fbx(filepath=str(project_path / object_path), **settings[object_settings])
		except Exception as e:
			bpy.context.window_manager.popup_menu(
				lambda self, ctx: (self.layout.label(text=str(e))) , 
				title=f"Error exporting '{object_path.name}'", 
				icon='ERROR')
			if center:
				obj.location = ox, oy, oz
			return {"CANCELLED"}

		if center:
			obj.location = ox, oy, oz

		bpy.context.window_manager.popup_menu(
			lambda self, ctx: (self.layout.label(text=f"Export of '{object_path.name}' was successful.")) , 
			title="Info", 
			icon='BLENDER')

		return {'FINISHED'}

class OLI_OT_export_selected_to_directory(bpy.types.Operator):
	"""Tooltip"""
	bl_idname = "export.export_selected_to_directory"
	bl_label = "Exports selected objects into their direcotries"

	def execute(self, context):
		temp_sel = list(context.selected_objects)
		for obj in temp_sel:
			if obj.toolchain_settings.export_path=="":
				continue
			select(obj)
			print(f"Exporting {obj.name}...")
			res = bpy.ops.export.to_directory()
			if res!={'FINISHED'}:
				return res
		select(*temp_sel)
		return {'FINISHED'}

class OLI_OT_open_exported_file(bpy.types.Operator):
	"""Open the exported file with the default viewer."""
	bl_idname = "olitools.open_exported_file"
	bl_label = "Open File"

	@classmethod
	def poll(cls, context):
		if context.scene.toolchain_settings.project_path=="":
			return False
		if context.active_object==None:
			return False
		if context.active_object.toolchain_settings.export_path=="":
			return False
		return True

	def execute(self, context):
		fbx_file_path = context.scene.toolchain_settings.project_path + "\\" + context.active_object.toolchain_settings.export_path
		subprocess.Popen(fbx_file_path, shell=True)
		return {'FINISHED'}

class OLI_OT_open_explorer_to_file(bpy.types.Operator):
	"""Open an Explorer Window to the file"""
	bl_idname = "olitools.open_explorer_to_file"
	bl_label = "Show in Explorer"

	@classmethod
	def poll(cls, context):
		if context.scene.toolchain_settings.project_path=="":
			return False
		if context.active_object==None:
			return False
		if context.active_object.toolchain_settings.export_path=="":
			return False
		return True

	def execute(self, context):
		fbx_file_path = Path(context.scene.toolchain_settings.project_path) / context.active_object.toolchain_settings.export_path
		print(f'explorer /select,"{fbx_file_path}"')
		subprocess.Popen(f'explorer /select,"{fbx_file_path}"')
		return {'FINISHED'}

# -----------------------------------------------------------------------
# Send to External
# -----------------------------------------------------------------------

class OLI_OT_export_to_substance_painter(bpy.types.Operator):
	"""Open the object in substance painter"""
	bl_idname = "olitools.export_to_substance_painter"
	bl_label = "Exports the active object to Substance Painter."

	@classmethod
	def poll(cls, context):
		addon_prefs = context.preferences.addons["rapid_gamedev_toolchain"].preferences
		if context.scene.toolchain_settings.project_path=="":
			return False
		if addon_prefs.painter_exe=="":
			return False
		if context.active_object is None:
			return False
		if context.active_object.type != "MESH":
			return False
		if context.active_object.toolchain_settings.export_path=="":
			return False
		return True

	def execute(self, context):
		print(f"App Name: {__name__}")
		addon_prefs = context.preferences.addons["rapid_gamedev_toolchain"].preferences

		# Export FBX File
		fbx_path = Path(context.scene.toolchain_settings.project_path) / context.active_object.toolchain_settings.export_path
		# if context.scene.external_apps_settings.export_directory=="":
		# 	fbx_path=Path(tempfile.gettempdir()) / "temp.fbx"
		# else:
		# 	fbx_path=Path(context.scene.external_apps_settings.export_directory) / (context.active_object.name.replace(".", "_")+".fbx")

		bpy.ops.export_scene.fbx(
			filepath=str(fbx_path),
			use_selection=True
			)

		# Generate Command List
		cmds=[]
		cmds.append(addon_prefs.painter_exe)
		cmds.append("--mesh")
		cmds.append(fbx_path)
		if context.scene.toolchain_settings.map_export_directory!="":
			cmds.append("--export-path")
			cmds.append(context.scene.toolchain_settings.map_export_directory)
		for cmd in cmds:
			print(f"'{cmd}'")
		try:
			subprocess.Popen(cmds)
		except Exception as e:
			bpy.context.window_manager.popup_menu(
				lambda self, ctx: (self.layout.label(text="Error starting painter!")) , 
				title="Error", 
				icon='ERROR')
		return {'FINISHED'}

class OLI_OT_export_to_affinity_designer(bpy.types.Operator):
	"""Export the UV as SVG and open in connected program"""
	bl_idname = "olitools.export_to_affinity_designer"
	bl_label = "Send UVs to Affinity Designer"

	@classmethod
	def poll(cls, context):
		addon_prefs = context.preferences.addons["rapid_gamedev_toolchain"].preferences
		if addon_prefs.designer_exe=="":
			return False
		if context.active_object is None:
			return False
		if context.active_object.type != "MESH":
			return False
		return True

	def execute(self, context):
		addon_prefs = context.preferences.addons["rapid_gamedev_toolchain"].preferences
		if context.scene.toolchain_settings.uv_export_directory=="":
			uv_path=Path(gettempdir()) / "temp.svg"
		else:
			svg_name = clean_name(context.active_object.name).replace(".", "_")+".svg"
			print(f"SVG Name: {svg_name}")
			uv_path=Path(context.scene.toolchain_settings.uv_export_directory) / svg_name

		res = context.scene.toolchain_settings.uv_resolution
		bpy.ops.uv.export_layout(filepath=str(uv_path), mode='SVG', size=(res, res))

		cmds=[]
		cmds.append(addon_prefs.designer_exe)
		cmds.append(uv_path)

		try:
			subprocess.Popen(cmds)
		except Exception as e:
			bpy.context.window_manager.popup_menu(
				lambda self, ctx: (self.layout.label(text="Error starting designer!")) , 
				title="Error", 
				icon='ERROR')
		return {'FINISHED'}


# -----------------------------------------------------------------------
# Panel
# -----------------------------------------------------------------------

class OLI_PT_export_to_directory(bpy.types.Panel):
	bl_space_type="VIEW_3D"
	bl_region_type="UI"
	bl_category="RGT"
	bl_label="Rapid Gamedev Toolchain"

	@classmethod
	def poll(cls, context):
		if context.active_object==None:
			return False
		return True

	def draw(self, context):
		if context.active_object==None:
			return
		box = self.layout.box()
		box.label(text="Export")
		box.enabled = context.active_object.type in exp_types
		sbox = box.split(factor=.9, align=True)
		sbox.prop(context.scene.toolchain_settings, "project_path", text="Project")
		sbox.operator("olitools.select_project_path", text="", icon="FILE_FOLDER")
		sbox = box.split(factor=.9, align=True)
		sbox.prop(context.object.toolchain_settings, "export_path", text="Object")
		sbox.operator("olitools.object_export_file_path_window", text="", icon="FILE_FOLDER")
		
		box.prop(context.scene.toolchain_settings, "export_format", text="Format")
		box.prop(context.object.toolchain_settings, "export_settings", text="Settings")
		box.prop(context.object.toolchain_settings, "center")

		col = box.column(align=True)
		col.scale_y = 2
		if len(context.selected_objects)<=1:
			col.operator("export.to_directory", text="Export", icon="EXPORT")
		else:
			col.operator("export.export_selected_to_directory", text="Export Selected", icon="EXPORT")


		row = box.row(align=True)
		row.operator("olitools.open_exported_file", text="Open File", icon="FILE_3D")
		row.operator("olitools.open_explorer_to_file", text="Open Explorer", icon="FILE_FOLDER")

		# --- Send to External ---
		box = self.layout.box()
		box.label(text="Substance Painter")
		# box.prop(context.scene.external_apps_settings, "export_directory", text="FBX Path")
		box.prop(context.scene.toolchain_settings, "map_export_directory", text="Texture Path")
		box.operator("olitools.export_to_substance_painter", text="Send Mesh to Painter")

		box = self.layout.box()
		box.label(text="Affinity Designer")
		box.prop(context.scene.toolchain_settings, "uv_export_directory", text="UV Path")
		box.prop(context.scene.toolchain_settings, "uv_resolution", text="UV File Res")
		box.operator("olitools.export_to_affinity_designer", text="Send UV to Designer")

# -----------------------------------------------------------------------
# Register
# -----------------------------------------------------------------------

blender_classes=[
	OLI_AP_rapid_gamedev_toolchain_settings,
	OLI_PG_export_directory_settings,
	OLI_PG_export_object_settings,
	OLI_OT_select_project_path,
	OLI_OT_object_export_file_path_window,
	OLI_OT_export_to_directory,
	OLI_OT_export_selected_to_directory,
	OLI_OT_open_explorer_to_file,
	OLI_OT_open_exported_file,
	OLI_OT_export_to_substance_painter,
	OLI_OT_export_to_affinity_designer,
	OLI_PT_export_to_directory
]


def register():
	for blender_class in blender_classes:
		bpy.utils.register_class(blender_class)
	bpy.types.Scene.toolchain_settings = bpy.props.PointerProperty(type = OLI_PG_export_directory_settings)
	bpy.types.Object.toolchain_settings = bpy.props.PointerProperty(type = OLI_PG_export_object_settings)

def unregister():
	del bpy.types.Scene.toolchain_settings
	del bpy.types.Object.toolchain_settings
	for blender_class in reversed(blender_classes):
		bpy.utils.unregister_class(blender_class)

if __name__ == "__main__":
	register()