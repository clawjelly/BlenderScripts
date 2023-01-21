# -------------------------------------------------------------
# Send to Substance
# -------------------------------------------------------------
# Version 0.1
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
	"name": "Send to Substance Painter",
	"author": "Oliver Reischl <clawjelly@gmail.net>",
	"version": (1, 0),
	"blender": (3, 3, 0),
	"location": "",
	"description": "Exports and sends an object straight to Substance Painter.",
	"category": "Export",
}

class OLI_AP_substance_painter_prefs(AddonPreferences):
	# this must match the add-on name, use '__package__'
	# when defining this in a submodule of a python package.
	bl_idname = __name__

	painter_exe: bpy.props.StringProperty(
		name="Exe Path",
		description="Substance Painter Executeable Path",
		subtype="FILE_PATH",
		default="",
		maxlen=0
	)

	def draw(self, context):
		box = self.layout.box()
		box.prop(self, "painter_exe", text="EXE Path")

class OLI_PG_substance_painter_settings(PropertyGroup):

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
		if context.scene.substance_painter_settings.export_directory=="":
			fbx_path=Path(tempfile.gettempdir()) / "temp.fbx"
		else:
			fbx_path=Path(context.scene.substance_painter_settings.export_directory) / (context.active_object.name.replace(".", "_")+".fbx")

		bpy.ops.export_scene.fbx(
			filepath=str(fbx_path),
			use_selection=True
			)

		# Generate Command List
		cmds=[]
		cmds.append(addon_prefs.painter_exe)
		cmds.append("--mesh")
		cmds.append(fbx_path)
		if context.scene.substance_painter_settings.map_export_directory!="":
			cmds.append("--export-path")
			cmds.append(context.scene.substance_painter_settings.map_export_directory)
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

class OLI_PT_send_to_substance(bpy.types.Panel):
	bl_space_type="VIEW_3D"
	bl_region_type="UI"
	bl_category="Tool"
	bl_label="Send to Substance"

	def draw(self, context):
		box = self.layout.box()
		box.prop(context.scene.substance_painter_settings, "export_directory", text="Mesh Path")
		box.prop(context.scene.substance_painter_settings, "map_export_directory", text="Texture Path")
		box.operator("olitools.export_to_substance_painter", text="Send to Substance")

blender_classes = [
	OLI_AP_substance_painter_prefs,
	OLI_PG_substance_painter_settings,
	OLI_OT_export_to_substance_painter,
	OLI_PT_send_to_substance
]

def register():
	for blender_class in blender_classes:
		bpy.utils.register_class(blender_class)
	bpy.types.Scene.substance_painter_settings = PointerProperty(type=OLI_PG_substance_painter_settings)

def unregister():
	del bpy.types.Scene.substance_painter_settings
	for blender_class in reversed(blender_classes):
		bpy.utils.unregister_class(blender_class)

if __name__ == "__main__":
	register()