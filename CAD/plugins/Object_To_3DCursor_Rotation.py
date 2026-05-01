bl_info = {
    "name": "Origin to 3D Cursor (Location + Rotation)",
    "author": "ELS",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "Object > Set Origin",
    "description": "Set origin to 3D cursor including rotation",
    "category": "Object",
}

import bpy
import mathutils

class OBJECT_OT_origin_to_cursor_full(bpy.types.Operator):

    #set name variables
    bl_idname = "object.origin_to_cursor_full"
    bl_label = "Origin to 3D Cursor (Location + Rotation)"
    bl_options = {'REGISTER', 'UNDO'}

    #on plugin run request
    def execute(self, context):
        #grab cursor transform
        cursor = context.scene.cursor
        cursor_matrix = cursor.matrix

        #for all selected objects
        for obj in context.selected_editable_objects:
            
            #skip non-meshes
            if obj.type != 'MESH':
                continue

            #store original world matrix + decompose it
            mw = obj.matrix_world.copy()
            loc, rot, scale = mw.decompose()

            #new origin rotation = cursor rotation
            new_rot = cursor_matrix.to_quaternion()

            #new origin location = cursor location
            new_loc = cursor.location.copy()

            #build new matrix_world
            new_mw = (
                mathutils.Matrix.Translation(new_loc) @
                new_rot.to_matrix().to_4x4() @
                mathutils.Matrix.Diagonal(scale.to_4d())
            )

            #compute delta transform for mesh data
            delta = new_mw.inverted() @ mw

            #apply delta to mesh data
            obj.data.transform(delta)

            #set new world matrix
            obj.matrix_world = new_mw

        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(
    OBJECT_OT_origin_to_cursor_full.bl_idname,
    text="Origin to 3D Cursor (Location + Rotation)"
    )

def register():
    bpy.utils.register_class(OBJECT_OT_origin_to_cursor_full)
    #put it inside the object menu and the right click menu (because putting it inside of object->set origin doesn't seem to be possible, which is strange)
    bpy.types.VIEW3D_MT_object.append(menu_func)
    bpy.types.VIEW3D_MT_object_context_menu.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func)
    bpy.utils.unregister_class(OBJECT_OT_origin_to_cursor_full)


if __name__ == "__main__":
    register()

##find where I want to put the menu
#print("----------------------------")
#stringss = dir(bpy.types)
##find = ["VIEW3D_MT_object_", "origin"]
#find = ["OBJECT_OT", "origin"]
#res = [x for x in stringss if any(y in x for y in find)]
#for a in res:
#    print(a)
##print(res)

