import os
import bpy
from bpy.app.handlers import persistent

bl_info = {
    "name": "auto reload scripts",
    "author": "Oliver Reischl <oliver@clawjelly.net>",
    "version": (1, 0),
    "blender": (2, 90, 0),
    "description": "Reloads Scripts",
    "category": "Scripting",
}

def reload_scripts_callback():
    """ Check modified external scripts in the scene and update if possible """

    # status=bpy.context.scene.get("auto_script_reload")
    if not bpy.context.scene.reloader_settings.is_active:
        print(f"Script Reload deactivated.")
        return(None)

    # print(f"Save Check: {status}")
    ctx = bpy.context.copy()
    #Ensure  context area is not None
    ctx['area'] = ctx['screen'].areas[0]
    for t in bpy.data.texts:
        if not t.is_modified:
            continue
        if t.is_in_memory:
            continue
        fp=bpy.path.abspath(t.filepath)
        if not os.path.exists(fp):
            continue

        print(f"Script Reloader: Updating {t.name}")
        # Change current context to contain a TEXT_EDITOR
        oldAreaType = ctx['area'].type
        ctx['area'].type = 'TEXT_EDITOR'
        ctx['edit_text'] = t
        try:
            bpy.ops.text.resolve_conflict(ctx, resolution='RELOAD')
        except:
            print(f"Problem reloading {t.name}")
        #Restore context
        ctx['area'].type = oldAreaType

        if bpy.context.scene.reloader_settings.run_script:
            if t.name==bpy.context.scene.reloader_settings.scripts:
                print(f"Running Script {t.name}")
                try:
                    filepath = bpy.path.abspath(t.filepath)
                    global_namespace = {"__file__": filepath, "__name__": "__main__"}
                    with open(filepath, 'rb') as file:
                        exec(compile(file.read(), filepath, 'exec'), global_namespace)
                except Exception as e:
                    print(f"ERROR: {e}")

    return(0.5)

@persistent
def reset_on_scene_reload_callback(scene):
    bpy.context.scene.reloader_settings.is_active=False

def update_script_enum(self, context):
    # returns a list of all script files
    return [ (t.name, t.name, t.filepath) for t in bpy.data.texts if t.name!="auto_reload_scripts.py"]

class OLI_PG_script_reloader(bpy.types.PropertyGroup):
    is_active : bpy.props.BoolProperty(
        name="Is Active", 
        default=False
        )
    # script : bpy.props.StringProperty(name="Script")
    scripts : bpy.props.EnumProperty(
        name="Script",
        description="Script to run automatically.",
        items=update_script_enum,
        default=None
        )
    run_script : bpy.props.BoolProperty(name="Run Script")

class OLI_OT_script_reloader(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "scripts.script_reloader"
    bl_label = "Script Reloader"

    is_active = True
    interval = 0.5

    number: bpy.props.IntProperty(
        name="Amount",
        default=1,
        min=0, max=10,
        description="This is how much stuff is stuff."
    )

    @classmethod
    def poll(cls, context):
        # return context.active_object is not None
        return True

    def register_reload(self):
        bpy.app.timers.register(reload_scripts_callback)
        print("Script Reload registered.") 

    def main(self, context):
        # status=context.scene.get("auto_script_reload")
        if context.scene.reloader_settings.is_active:
            context.scene.reloader_settings.is_active=False
        else:
            context.scene.reloader_settings.is_active=True
            self.register_reload()
        
    def execute(self, context):
        self.main(context)
        return {'FINISHED'}

class OLI_OT_relative_script_path(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "scripts.relative_script_path"
    bl_label = "Set script path relative"

    def execute(self, context):
        t=bpy.data.texts[bpy.context.scene.reloader_settings.scripts]
        print(f"File {t.name} at {t.filepath}")
        try:
            t.filepath = bpy.path.relpath(t.filepath)
        except:
            bpy.context.window_manager.popup_menu(
                lambda self, ctx: (self.layout.label(text="Setting relative did not work.")) , 
                title="Warning", 
                icon='ERROR')
        return {'FINISHED'}

class OLI_OT_absolute_script_path(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "scripts.absolute_script_path"
    bl_label = "Set script path absolute"

    def execute(self, context):
        t=bpy.data.texts[bpy.context.scene.reloader_settings.scripts]
        print(f"File {t.name} at {t.filepath}")
        try:
            t.filepath = bpy.path.abspath(t.filepath)
        except:
            bpy.context.window_manager.popup_menu(
                lambda self, ctx: (self.layout.label(text="Setting absolute did not work.")) , 
                title="Warning", 
                icon='ERROR')
        return {'FINISHED'}


class VIEW3D_PT_script_reloader(bpy.types.Panel):
    bl_space_type="TEXT_EDITOR"
    bl_region_type="UI"
    bl_category="Text"
    bl_label="Script Reloader"

    @classmethod
    def poll(cls, context):
        # return context.active_object is not None
        return len(bpy.data.texts)>0

    def draw(self, context):
        layout = self.layout
        box=layout.box()
        box.operator("scripts.script_reloader", text="Toggle Script Reloader")
        status="Status: "+("active" if context.scene.reloader_settings.is_active else "inactive")
        box.label(text=status)
        box.prop(context.scene.reloader_settings, "run_script")
        box.prop(context.scene.reloader_settings, "scripts")
        if context.scene.reloader_settings.scripts!="":
            tfile = bpy.data.texts[context.scene.reloader_settings.scripts]
            if tfile!=None:
                fpath=tfile.filepath
                layout.separator()
                box=layout.box()
                box.label(text=f"Script Filepath:")
                box.label(text=f"{fpath}")
                row=box.row()
                row.operator("scripts.relative_script_path", text="Relative")
                row.operator("scripts.absolute_script_path", text="Absolute")

blender_classes=[
    OLI_PG_script_reloader,
    OLI_OT_script_reloader,
    OLI_OT_relative_script_path,
    OLI_OT_absolute_script_path,
    VIEW3D_PT_script_reloader
]

def register():
    for blender_class in blender_classes:
        bpy.utils.register_class(blender_class)
    bpy.types.Scene.reloader_settings = bpy.props.PointerProperty(type=OLI_PG_script_reloader)
    bpy.app.handlers.load_post.append(reset_on_scene_reload_callback)

def unregister():
    del bpy.types.Scene.reloader_settings
    for blender_class in reversed(blender_classes):
        bpy.utils.unregister_class(blender_class)
    bpy.app.handlers.load_post.pop(reset_on_scene_reload_callback)

if __name__ == "__main__":
    print("Auto Reloader started!") 
    register()
    bpy.context.scene.reloader_settings.is_active=False
    bpy.context.scene.reloader_settings.run_script=False
    # unregister()