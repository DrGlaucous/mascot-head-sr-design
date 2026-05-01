bl_info = {
    "name": "Boolean Intersect Splitter",
    "author": "ChatGPT",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Tool Tab",
    "description": "Split a mesh into pieces using boolean intersect with a collection",
    "category": "Object",
}

import bpy


class OBJECT_OT_boolean_intersect_split(bpy.types.Operator):
    bl_idname = "object.boolean_intersect_split"
    bl_label = "Split Mesh by Collection (Intersect)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        source_obj = context.active_object
        collection = context.scene.boolean_split_collection

        if not source_obj or source_obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}

        if not collection:
            self.report({'ERROR'}, "No collection selected")
            return {'CANCELLED'}

        # Store original collection
        target_collection = source_obj.users_collection[0]

        created_objects = []

        for cutter in collection.objects:
            if cutter.type != 'MESH':
                continue

            # Duplicate source object
            new_obj = source_obj.copy()
            new_obj.data = source_obj.data.copy()
            new_obj.name = f"{source_obj.name}_part_{cutter.name}"

            target_collection.objects.link(new_obj)

            # Add boolean modifier
            bool_mod = new_obj.modifiers.new(
                name="BooleanIntersect",
                type='BOOLEAN'
            )
            bool_mod.operation = 'INTERSECT'
            bool_mod.object = cutter
            bool_mod.solver = 'EXACT'

            # Apply modifier
            context.view_layer.objects.active = new_obj
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)

            created_objects.append(new_obj)

        # Restore active object
        context.view_layer.objects.active = source_obj

        self.report({'INFO'}, f"Created {len(created_objects)} pieces")
        return {'FINISHED'}


class VIEW3D_PT_boolean_intersect_panel(bpy.types.Panel):
    bl_label = "Boolean Splitter"
    bl_idname = "VIEW3D_PT_boolean_intersect_splitter"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "boolean_split_collection")
        layout.operator("object.boolean_intersect_split")


def register():
    bpy.utils.register_class(OBJECT_OT_boolean_intersect_split)
    bpy.utils.register_class(VIEW3D_PT_boolean_intersect_panel)

    bpy.types.Scene.boolean_split_collection = bpy.props.PointerProperty(
        name="Cutter Collection",
        type=bpy.types.Collection
    )


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_boolean_intersect_split)
    bpy.utils.unregister_class(VIEW3D_PT_boolean_intersect_panel)

    del bpy.types.Scene.boolean_split_collection


if __name__ == "__main__":
    register()