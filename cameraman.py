import bpy
import math
import viewlayerman
import utils
import importlib

# Just some magic strings
MULTICAM = "Multicam"
MULTI_VIEW_LAYER = "Multi View Layer"
MAIN = "Main"
SUBJECT = "Subject"

importlib.reload(viewlayerman)
importlib.reload(utils)

def create_rotated_object(r, theta, phi, object_data, rotation_mode = "XYZ"):
    x = math.sin(math.radians(phi)) * \
        math.cos(math.radians(theta)) * r
    y = math.sin(math.radians(phi)) * \
        math.sin(math.radians(theta)) * r
    z = math.cos(math.radians(phi)) * r

    # create the object
    obj = bpy.data.objects.new(utils.angles_to_str(theta, phi), object_data)
    obj.location = (x, y, z)
    obj.rotation_mode = rotation_mode
    obj.rotation_euler = (
        math.radians(phi), 0, math.radians(theta))

    return obj


def generate_multicam(distance: int = 12, parallel_count: int = 9, meridian_count: int = 16):
    scn = bpy.context.scene
    collection = bpy.data.collections.new(MULTICAM)
    scn.collection.children.link(collection)

    def create_camera(theta, phi):
        name = utils.angles_to_str(theta, phi)

        # create the camera
        cam = bpy.data.cameras.new(name)
        cam.lens = 31.18  # = 60 degrees FOV
        z_angle = (theta + 90) % 360
        cam_obj = create_rotated_object(distance, z_angle, phi, cam)

        collection.objects.link(cam_obj)

    for p in range(-(parallel_count // 2), parallel_count // 2 + 1): # Exclude poles
        for m in range(0, meridian_count):
            theta = 360 / meridian_count * m
            phi = 90 - (180 / (parallel_count - 1) * p)
            create_camera(theta, phi)

def prepare_view_layer():
    def recursive_remove(c):
        for sub in c.children:
            recursive_remove(sub)
        for o in c.objects:
            bpy.data.objects.remove(o)
        bpy.data.collections.remove(c)

    scn = bpy.context.scene
    for vl in scn.view_layers:
        if vl.name != MAIN:
            scn.view_layers.remove(vl)
    if MULTI_VIEW_LAYER in scn.collection.children:
        recursive_remove(scn.collection.children[MULTI_VIEW_LAYER])


def generate_multi_view_layer(parallel_count: int = 9, meridian_count: int = 16):
    context = bpy.context
    scn = context.scene

    parent_collection = bpy.data.collections.new(MULTI_VIEW_LAYER)
    scn.collection.children.link(parent_collection)

    def create_object(theta, phi):
        name = f"{theta}, {phi}"

        viewlayer = viewlayerman.copy_from_main_layer(name)
        collection = bpy.data.collections.new(name)
        parent_collection.children.link(collection)

        subject = bpy.data.objects[SUBJECT]

        # duplicate the linked object
        new_obj = create_rotated_object(0, theta, phi, subject.data, "ZYX")

        collection.objects.link(new_obj)
    
    for p in range(-(parallel_count // 2), parallel_count // 2 + 1): # Exclude poles
        for m in range(0, meridian_count):
            theta = 360 / meridian_count * m
            phi = 180 / (parallel_count - 1) * p
            create_object(theta, phi)

    for vl in context.scene.view_layers:
        vl.layer_collection.children[SUBJECT].exclude = True
        parent_layer_collection = vl.layer_collection.children[MULTI_VIEW_LAYER]
        for lc in parent_layer_collection.children:
            if lc.name == vl.name:
                lc.exclude = False
            else:
                lc.exclude = True

