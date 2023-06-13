# -------------------------------------------------------------
# Rapid Gamedev Toolchain
# -------------------------------------------------------------
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

import json, subprocess
from pathlib import Path
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
# Functions
# -----------------------------------------------------------------------

def select(*objs):
	bpy.ops.object.select_all(action='DESELECT')
	for obj in objs:
		obj.select_set(True)

def get_hierarchy(*objs):
	newobjs=[]    
	testobjs=list(objs)
	while testobjs:
		obj=testobjs.pop()
		testobjs.extend(obj.children)
		newobjs.append(obj)
	return newobjs

def get_fbx_default_settings():
	return {
		# "filepath" = 'C:\\UnityProjects\\Verteges\\Assets\\Vertify\\Models\\Accessories\\Hands.fbx',
		"use_selection" : True,
		"use_visible" : False,
		"use_active_collection" : False,
		"global_scale" : 1.0,
		"apply_unit_scale" : True,
		"apply_scale_options" : 'FBX_SCALE_NONE',
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

def save_fbx_settings(settings = None):
	"""Saves the fbx export settings. If none are given, it saves default settings."""
	cPath=Path(bpy.utils.resource_path(type="USER")) / "config"

	if settings == None:
		settings = dict()
		settings["default"] = get_fbx_default_settings()
		settings["default"]["object_types"]=list(settings["default"]["object_types"])

	with open(cPath / "ot_fbx_settings.json", "w") as jsonfile:
		json.dump(settings, jsonfile, indent=2)

def load_fbx_settings():
	"""Loads the fbx export settings. If none are found, it creates default settings"""
	cPath=Path(bpy.utils.resource_path(type="USER")) / "config" / "ot_fbx_settings.json"

	if not cPath.exists():
		save_fbx_settings() # save defaults

	with open(cPath) as jsonfile:
		settings = json.load(jsonfile)
		for key, item in settings.items():
			settings[key]["object_types"]=set(settings[key]["object_types"])

	return settings

def check_for_export(obj):
	if obj.data.shape_keys!=None and len(obj.modifiers)!=0:
		return f"- {obj.name} has shape keys and modifiers, shape keys won't be exported."
	return ""

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

	project_path: bpy.props.StringProperty(
		name="Export Path",
		description="The filepath of the exports.",
		default="",
		subtype="NONE",
		maxlen=0,
		update = update_project_path
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
		obj_path = Path(context.active_object.toolchain_settings.export_path)
		if context.scene.toolchain_settings.project_path!="":
			prj_path = Path(context.scene.toolchain_settings.project_path)
			self["export_path"] = str(obj_path.relative_to(prj_path))

	def settings_callback(self, context):
		temp = [(key, key, "") for key, item in load_fbx_settings().items()]
		return temp

	export_path: bpy.props.StringProperty(
		name="Export Path",
		description="The export path relative to the project to directory.",
		default="",
		# subtype="FILE_PATH",
		subtype="NONE",
		maxlen=0,
		# set = set_obj_export_path,
		update = update_obj_export_path
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
		default="*.fbx",
		options={'HIDDEN'},
		maxlen=255,  # Max internal buffer length, longer would be clamped.
	)

	filepath: StringProperty()
	filename:  StringProperty()
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
		if context.active_object.toolchain_settings.export_path=="":
			self.filepath = context.scene.toolchain_settings.project_path + "\\" + context.active_object.name + ".fbx"
		else:
			self.filepath = context.scene.toolchain_settings.project_path + "\\" + context.active_object.toolchain_settings.export_path
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}

	def execute(self, context):
		"""This is called after the window opened."""
		if self.filepath[-4:]!=".fbx":
			self.filepath+=".fbx"
		context.active_object.toolchain_settings.export_path = abspath(self.filepath)
		return {'FINISHED'}

# -----------------------------------------------------------------------
# Export
# -----------------------------------------------------------------------

class OLI_OT_export_to_directory(bpy.types.Operator):
	"""Exports the object to an FBX inside the stored directory."""
	bl_idname = "export.to_directory"
	bl_label = "Exports object to an FBX with defined settings."

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
		settings = load_fbx_settings()
		project_path = Path(context.scene.toolchain_settings.project_path)
		object_path = Path(context.active_object.toolchain_settings.export_path)
		if object_path.suffix!=".fbx":
			object_path=object_path.with_suffix(".fbx")
		object_settings = context.active_object.toolchain_settings.export_settings
		if object_settings not in settings:
			bpy.context.window_manager.popup_menu(
				lambda self, ctx: (self.layout.label(text=f"Settings '{object_settings}' not found!")) , 
				title="Error", 
				icon='ERROR')
			return {"CANCELLED"}

		center = context.active_object.toolchain_settings.center

		# We want to export the full hierarchy. No idea what that isn't even considered in the exporter itself.
		obj = context.active_object
		select(*get_hierarchy(context.active_object))
		
		# Check for any export issues.
		issues = []
		for cobj in context.selected_objects:
			msg = check_for_export(cobj)
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

		try:
			bpy.ops.export_scene.fbx(filepath=str(project_path / object_path), **settings[object_settings])
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

class OLI_OT_open_exported_file(bpy.types.Operator):
	"""Open the exported file with the default viewer."""
	bl_idname = "olitools.open_exported_file"
	bl_label = "Open File"

	@classmethod
	def poll(cls, context):
		return context.active_object is not None

	def execute(self, context):
		fbx_file_path = context.scene.toolchain_settings.project_path + "\\" + context.active_object.toolchain_settings.export_path
		print(fbx_file_path)
		subprocess.Popen(fbx_file_path, shell=True)
		return {'FINISHED'}

class OLI_OT_open_explorer_to_file(bpy.types.Operator):
	"""Open an Explorer Window to the file"""
	bl_idname = "olitools.open_explorer_to_file"
	bl_label = "Show in Explorer"

	@classmethod
	def poll(cls, context):
		return context.active_object is not None

	def execute(self, context):
		fbx_file_path = Path(context.scene.toolchain_settings.project_path) / context.active_object.toolchain_settings.export_path
		print(f'explorer /select,"{fbx_file_path}"')
		subprocess.Popen(f'explorer /select,"{fbx_file_path}"')
		return {'FINISHED'}

# -----------------------------------------------------------------------
# Send to External
# -----------------------------------------------------------------------

class OLI_OT_export_to_substance_painter(bpy.types.Operator):
	"""Tooltip"""
	bl_idname = "olitools.export_to_substance_painter"
	bl_label = "Exports the active object to Substance Painter."

	@classmethod
	def poll(cls, context):
		addon_prefs = context.preferences.addons["rapid_gamedev_toolchain"].preferences
		if addon_prefs.painter_exe=="":
			return False
		if context.active_object is None:
			return False
		if context.active_object.type != "MESH":
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
	"""Tooltip"""
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
			uv_path=Path(tempfile.gettempdir()) / "temp.svg"
		else:
			uv_path=Path(context.scene.toolchain_settings.uv_export_directory) / (context.active_object.name.replace(".", "_")+".svg")

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
	bl_category="Tool"
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
		sbox = box.split(factor=.9, align=True)
		sbox.prop(context.scene.toolchain_settings, "project_path", text="Project")
		sbox.operator("olitools.select_project_path", text="", icon="FILE_FOLDER")
		sbox = box.split(factor=.9, align=True)
		sbox.prop(context.object.toolchain_settings, "export_path", text="Object")
		sbox.operator("olitools.object_export_file_path_window", text="", icon="FILE_FOLDER")
		
		box.prop(context.object.toolchain_settings, "export_settings", text="Settings")
		box.prop(context.object.toolchain_settings, "center")

		col = box.column(align=True)
		col.scale_y = 2
		col.operator("export.to_directory", text="Export", icon="EXPORT")

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
		box.prop(context.scene.toolchain_settings, "uv_resolution", text="File Res")
		box.operator("olitools.export_to_affinity_designer", text="Send UV to Designer")


blender_classes=[
	OLI_AP_rapid_gamedev_toolchain_settings,
	OLI_PG_export_directory_settings,
	OLI_PG_export_object_settings,
	OLI_OT_select_project_path,
	OLI_OT_object_export_file_path_window,
	OLI_OT_export_to_directory,
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