import logging

import bmesh
import bpy

"""
Removes each pair of faces of all objects that matches by all vertices. Intended to remove inner faces.
"""

bl_info = {
    "name": "CollapseFaces",
    "blender": (2, 80, 0),  # look to register - there is the hack, so it's recognized as compatible by 2.79 too
    "category": "Object",
}

log = logging.getLogger(__name__)


class CollapseFaces001(bpy.types.Operator):
    """Collapse Faces"""
    bl_idname = "object.collapse_faces"
    bl_label = "Collapse Adjecent Faces"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        def show(message):
            context.window_manager.popup_menu(lambda a, b: {}, title=message)

        print(" ================ Collapse faces! ================")

        context = context  # type: bpy.types.Context
        scene = context.scene
        collapsed = 0

        if bpy.app.version[1] < 80:
            # https://svn.blender.org/svnroot/bf-blender/trunk/blender/source/blender/bmesh/intern/bmesh_operator_api.h
            DEL_VERTS = 1
            DEL_EDGES = 2
            DEL_ONLYFACES = 3
            DEL_EDGESFACES = 4
            DEL_FACES = 5
            DEL_ALL = 6
            DEL_ONLYTAGGED = 7
            mult_matrix = lambda matrix, vector: matrix * vector
        else:
            DEL_VERTS = "VERTS"
            DEL_EDGES = "EDGES"
            DEL_ONLYFACES = "ONLYFACES"
            DEL_EDGESFACES = "EDGESFACES"
            DEL_FACES = "FACES"
            DEL_ALL = "ALL"
            DEL_ONLYTAGGED = "ONLYTAGGED"
            mult_matrix = lambda matrix, vector: matrix @ vector

        group_counts = {}
        for phase in [0, 1]:
            for group in group_counts.items():
                print("%s: %s" % group)
            for o in scene.objects:  # type: bpy.types.Object
                if o.type == "MESH":
                    mesh = bmesh.new()
                    mesh.from_mesh(o.data)

                    faces_to_delete = []

                    for face in mesh.faces:
                        print("Face: %s" % face)
                        coords = (
                            mult_matrix(o.matrix_world, v.co)
                            for v in face.verts
                        )
                        sorted_coords = (
                            vector_to_key(wc)
                            for wc in sort_vectors(coords)
                        )
                        group_key = tuple(sorted_coords)
                        matched_groups = group_counts.get(group_key, 0)
                        if phase == 0:
                            group_counts[group_key] = matched_groups + 1
                        elif phase == 1:
                            if matched_groups > 1:
                                print("enqueue to delete face %s with group %s" % (face, group_key))
                                faces_to_delete.append(face)

                    if len(faces_to_delete) > 0:
                        bmesh.ops.delete(mesh, geom=faces_to_delete, context=DEL_FACES)
                        mesh.to_mesh(o.data)
                        collapsed += len(faces_to_delete)

        show("Faces collapsed: %s" % collapsed)
        return {'FINISHED'}


def vector_to_key(v):
    # in 2.79 floating error is too much and we need to round to match adjacent sides of cube cloned with CTRL.
    # in 2.8 it works without rounding at all.
    return (
        int(round(v.x, 5) * 10000.0),
        int(round(v.y, 5) * 10000.0),
        int(round(v.z, 5) * 10000.0)
    )


def sort_vectors(vectors):
    return sorted(vectors, key=lambda v: v.x * 10000 + v.y * 100 + v.z)


def register():
    bl_info['blender'] = getattr(bpy.app, "version")
    bpy.utils.register_class(CollapseFaces001)


def unregister():
    bpy.utils.unregister_class(CollapseFaces001)

