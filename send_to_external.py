# -------------------------------------------------------------
# Send to External App
# -------------------------------------------------------------
# Ver 0.2
# - Adding Affinity Designer usability
# Ver 0.1
# - First Version
# -------------------------------------------------------------

import json, subprocess, tempfile
import bpy
from pathlib import Path
from bpy_extras.io_utils import unique_name, ExportHelper, ImportHelper
from bpy.types import PropertyGroup, AddonPreferences
from bpy.props import (
	StringProperty, 
	BoolProperty, 
	EnumProperty, 
	PointerProperty, 
	CollectionProperty, 
	IntProperty
	)

bl_info = {
	"name": "Send to External Apps",
	"author": "Oliver Reischl <clawjelly@gmail.net>",
	"version": (0, 2),
	"blender": (3, 3, 0),
	"location": "",
	"description": "Exports and sends an object data to external application.",
	"category": "Export",
}

class OLI_AP_external_apps_prefs(AddonPreferences):
	# this must match the add-on name, use '__package__'
	# when defining this in a submodule of a python package.
	bl_idname = __name__

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

class OLI_PG_external_apps_settings(PropertyGroup):

	export_directory: bpy.props.StringProperty(
		name="Mesh Export Directory",
		description="If this is empty, it will export the mesh to the system's temporary folder",
		default="",
		subtype="DIR_PATH",
		maxlen=0
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

class OLI_OT_export_to_substance_painter(bpy.types.Operator):
	"""Tooltip"""
	bl_idname = "olitools.export_to_substance_painter"
	bl_label = "Exports the active object to Substance Painter."

	@classmethod
	def poll(cls, context):
		addon_prefs = context.preferences.addons[__name__].preferences
		if addon_prefs.painter_exe=="":
			return False
		if context.active_object is None:
			return False
		if context.active_object.type != "MESH":
			return False
		return True

	def execute(self, context):
		addon_prefs = context.preferences.addons[__name__].preferences

		# Export FBX File
		if context.scene.external_apps_settings.export_directory=="":
			fbx_path=Path(tempfile.gettempdir()) / "temp.fbx"
		else:
			fbx_path=Path(context.scene.external_apps_settings.export_directory) / (context.active_object.name.replace(".", "_")+".fbx")

		bpy.ops.export_scene.fbx(
			filepath=str(fbx_path),
			use_selection=True
			)

		# Generate Command List
		cmds=[]
		cmds.append(addon_prefs.painter_exe)
		cmds.append("--mesh")
		cmds.append(fbx_path)
		if context.scene.external_apps_settings.map_export_directory!="":
			cmds.append("--export-path")
			cmds.append(context.scene.external_apps_settings.map_export_directory)
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
		addon_prefs = context.preferences.addons[__name__].preferences
		if addon_prefs.designer_exe=="":
			return False
		if context.active_object is None:
			return False
		if context.active_object.type != "MESH":
			return False
		return True

	def execute(self, context):
		addon_prefs = context.preferences.addons[__name__].preferences
		if context.scene.external_apps_settings.uv_export_directory=="":
			uv_path=Path(tempfile.gettempdir()) / "temp.svg"
		else:
			uv_path=Path(context.scene.external_apps_settings.uv_export_directory) / (context.active_object.name.replace(".", "_")+".svg")

		res = context.scene.external_apps_settings.uv_resolution
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

class OLI_PT_send_to_external(bpy.types.Panel):
	bl_space_type="VIEW_3D"
	bl_region_type="UI"
	bl_category="Tool"
	bl_label="Send to External"

	@classmethod
	def poll(cls, context):
		addon_prefs = context.preferences.addons[__name__].preferences
		if addon_prefs.designer_exe=="" and addon_prefs.painter_exe=="":
			return False
		if context.active_object is None:
			return False
		if context.active_object.type != "MESH":
			return False
		return True

	def draw(self, context):
		box = self.layout.box()
		box.prop(context.scene.external_apps_settings, "export_directory", text="FBX Path")
		box.prop(context.scene.external_apps_settings, "map_export_directory", text="Texture Path")
		box.operator("olitools.export_to_substance_painter", text="Send Mesh to Painter")

		box = self.layout.box()
		box.prop(context.scene.external_apps_settings, "uv_export_directory", text="UV Path")
		box.prop(context.scene.external_apps_settings, "uv_resolution", text="File Res")
		box.operator("olitools.export_to_affinity_designer", text="Send UV to Designer")

blender_classes = [
	OLI_AP_external_apps_prefs,
	OLI_PG_external_apps_settings,
	OLI_OT_export_to_substance_painter,
	OLI_OT_export_to_affinity_designer,
	OLI_PT_send_to_external
]

def register():
	for blender_class in blender_classes:
		bpy.utils.register_class(blender_class)
	bpy.types.Scene.external_apps_settings = PointerProperty(type=OLI_PG_external_apps_settings)

def unregister():
	del bpy.types.Scene.external_apps_settings
	for blender_class in reversed(blender_classes):
		bpy.utils.unregister_class(blender_class)

if __name__ == "__main__":
	register()