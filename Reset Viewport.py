import bpy


vm = ((0.41, -0.4017, 0.8188, 0.0),(0.912, 0.1936, -0.3617, 0.0),(-0.0133, 0.8959, 0.4458, 0.0),(0.0, 0.0, -14.9892, 1.0))

for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        v3d = area.spaces[0].region_3d
        if v3d :
            v3d.view_matrix = vm
            v3d.view_perspective = 'PERSP'