import bpy

class C3_MT_menu(bpy.types.Menu):
    bl_idname = "C3_MT_menu"
    bl_label = "C3 Add-On"
    
    def draw(self, context):
        layout = self.layout
        layout.operator("import_scene.c3_model", text="Import .C3 Model")
        layout.operator("import_scene.c3_parts", text="Import .C3 Model Parts")
        layout.separator()
        layout.operator("import_scene.c3_texture", text="Import Texture")
        layout.separator()
        layout.operator("import_scene.c3_animation", text="Import Animation")

def menu_func(self, context):
    self.layout.menu(C3_MT_menu.bl_idname)

def register():
    bpy.utils.register_class(C3_MT_menu)
    bpy.types.TOPBAR_MT_editor_menus.append(menu_func)

def unregister():
    bpy.types.TOPBAR_MT_editor_menus.remove(menu_func)
    bpy.utils.unregister_class(C3_MT_menu)
