# -------------------------------------------------------------
# Olitools Exporter
# -------------------------------------------------------------
# Version 0.1
# -------------------------------------------------------------

bl_info = {
	"name": "Olitools Export",
	"author": "Oliver Reischl <clawjelly@gmail.net>",
	"version": (0, 1),
	"blender": (3, 00, 0),
	"description": "Exports objects directly without asking for location.",
	"category": "Assets",
}

import json
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
# Scene Settings
# -----------------------------------------------------------------------


class OLI_PG_export_directory_settings(PropertyGroup):
	
	def update_project_path(self, context):
		value = context.scene.toolchain_settings.project_path
		self["project_path"] = str(Path(abspath(value)).resolve())

	project_path: bpy.props.StringProperty(
		name="Export Path",
		description="The filepath of the exports.",
		default="",
		subtype="DIR_PATH",
		maxlen=0,
		update = update_project_path
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
# Export
# -----------------------------------------------------------------------

class OLI_OT_export_to_directory(bpy.types.Operator):
	"""Exports the object to an FBX inside the stored directory. If this doesn't exists, it asks for a path."""
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

class OLI_OT_object_export_file_path_window(bpy.types.Operator):
	"""Opens a better file select window"""
	bl_idname = "olitools.object_export_file_path_window"  # important since its how bpy.ops.import_test.some_data is constructed
	bl_label = "Set Export Path"

	# ExportHelper mixin class uses this
	filename_ext = ".fbx"

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
		# if context.active_object.toolchain_settings.export_path=="":
		# 	return False
		return True

	def invoke(self, context, _event):
		"""This is called before any window opens."""
		if context.active_object.toolchain_settings.export_path=="":
			self.filepath = context.scene.toolchain_settings.project_path + "\\" + context.active_object.name + ".fbx"
		else:
			self.filepath = context.scene.toolchain_settings.project_path + "\\" + context.active_object.toolchain_settings.export_path
		context.window_manager.fileselect_add(self)
		if self.filepath[-4:]!=".fbx":
			self.filepath+=".fbx"
		return {'RUNNING_MODAL'}

	def execute(self, context):
		"""This is called after the window opened."""
		root = Path(self.directory)
		print(root)
		if not root.is_dir():
			bpy.context.window_manager.popup_menu(
				lambda self, ctx: (self.layout.label(text="Not a folder.")) , 
				title="Warning", 
				icon='ERROR')
			return {'CANCELLED'}

		wm = context.window_manager
		context.active_object.toolchain_settings.export_path = abspath(self.filepath)
		return {'FINISHED'}

class OLI_OT_open_exported_file(bpy.types.Operator):
	"""Tooltip"""
	bl_idname = "olitools.open_exported_file"
	bl_label = "Open File"

	@classmethod
	def poll(cls, context):
		return context.active_object is not None

	def execute(self, context):
		pass
		return {'FINISHED'}

class OLI_PT_export_to_directory(bpy.types.Panel):
	bl_space_type="VIEW_3D"
	bl_region_type="UI"
	bl_category="Tool"
	bl_label="Export FBX to Directory"

	@classmethod
	def poll(cls, context):
		if context.active_object==None:
			return False
		return True

	def draw(self, context):
		if context.active_object==None:
			return
		box = self.layout.box()
		box.prop(context.scene.toolchain_settings, "project_path", text="Project")
		
		sbox = box.split(factor=.9, align=True)
		sbox.prop(context.object.toolchain_settings, "export_path", text="Object")
		sbox.operator("olitools.object_export_file_path_window", text="", icon="FILE_FOLDER")
		
		box.prop(context.object.toolchain_settings, "export_settings", text="Settings")
		box.prop(context.object.toolchain_settings, "center")
		box.scale_y=2
		box.operator("export.to_directory", text="Export")
		box.scale_y=1


blender_classes=[
	OLI_PG_export_directory_settings,
	OLI_PG_export_object_settings,
	OLI_OT_export_to_directory,
	OLI_OT_object_export_file_path_window,
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
	# save_fbx_settings()
	# fbxpath = r"H:\Projects\UnityProjects\EnterTheStarship\Assets\ShipModules\Pentacorridor\Models\PentaCorridor_Door01.fbx"
	# bpy.ops.export_scene.fbx(filepath=fbxpath, **fbx_export_settings)
