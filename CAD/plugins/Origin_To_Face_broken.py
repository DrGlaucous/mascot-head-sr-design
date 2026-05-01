bl_info = {
    "name": "Align Origin to Face",
    "author": "ELS",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Object > Align Origin to Face",
    "description": "Align object origin and rotation to selected face normal",
    "category": "Object",
}

import bpy
import bmesh
from mathutils import Matrix, Vector


class OBJECT_OT_align_origin_to_face(bpy.types.Operator):
    bl_idname = "object.align_origin_to_face"
    bl_label = "Align Origin to Face"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object

        if obj is None or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}

        if context.mode != 'EDIT_MESH':
            self.report({'ERROR'}, "Must be in Edit Mode with a face selected")
            return {'CANCELLED'}

        bm = bmesh.from_edit_mesh(obj.data)
        faces = [f for f in bm.faces if f.select]

        if not faces:
            self.report({'ERROR'}, "No face selected")
            return {'CANCELLED'}

        face = faces[0]  # Use first selected face

        # Get face center and normal in object space
        face_center = face.calc_center_median()
        face_normal = face.normal.normalized()

        # Create a rotation matrix that aligns Z axis to face normal
        up = face_normal
        # Generate arbitrary tangent
        tangent = up.orthogonal().normalized()
        bitangent = up.cross(tangent).normalized()

        rot_matrix = Matrix((
            tangent,
            bitangent,
            up
        )).transposed()

        # Convert to 4x4
        rot_matrix_4x4 = rot_matrix.to_4x4()

        # Compute world transform
        world_matrix = obj.matrix_world @ Matrix.Translation(face_center)

        # Apply rotation in world space
        new_matrix = Matrix.Translation(world_matrix.to_translation()) @ rot_matrix_4x4

        # Move geometry so face sits at origin after reset
        bpy.ops.object.mode_set(mode='OBJECT')

        # Apply transform to mesh data
        mesh = obj.data
        transform = new_matrix.inverted() @ obj.matrix_world

        mesh.transform(transform)
        obj.matrix_world = new_matrix

        return {'FINISHED'}


# def menu_func(self, context):
#     self.layout.operator(OBJECT_OT_align_origin_to_face.bl_idname)


# def register():
#     bpy.utils.register_class(OBJECT_OT_align_origin_to_face)
#     bpy.types.VIEW3D_MT_object.append(menu_func)


# def unregister():
#     bpy.utils.unregister_class(OBJECT_OT_align_origin_to_face)
#     bpy.types.VIEW3D_MT_object.remove(menu_func)


def menu_func(self, context):
    self.layout.operator(OBJECT_OT_align_origin_to_face.bl_idname)

def register():
    bpy.utils.register_class(OBJECT_OT_align_origin_to_face)
    bpy.types.VIEW3D_MT_edit_mesh_faces.append(menu_func)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_align_origin_to_face)
    bpy.types.VIEW3D_MT_edit_mesh_faces.remove(menu_func)
    

if __name__ == "__main__":
    register()