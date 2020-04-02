import bpy
import os
import math
import utils
import importlib

importlib.reload(utils)

def single_render_dimensions():
    rdb = bpy.context.scene.renderborder
    return (rdb.max_x - rdb.min_x, rdb.max_y - rdb.min_y)

def final_output_dimensions(row_count: int, column_count: int):
    iw, ih = single_render_dimensions()
    return (iw * column_count, ih * row_count)


def prepare_compositor():
    # switch on nodes and get reference
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree

    # clear default nodes
    for node in tree.nodes:
        tree.nodes.remove(node)


def generate_background_node(row_count: int, column_count: int):
    final_w, final_h = final_output_dimensions(row_count, column_count)
    
    context = bpy.context
    tree = context.scene.node_tree
    mask = tree.nodes.new('CompositorNodeMask')
    mask.size_source = "FIXED"
    mask.size_x = final_w
    mask.size_y = final_h

    set_alpha = tree.nodes.new('CompositorNodeSetAlpha')
    set_alpha.inputs[1].default_value = 0

    tree.links.new(mask.outputs[0], set_alpha.inputs[0])
    return set_alpha

def get_ouptut_path():
    filename = bpy.path.basename(bpy.data.filepath)
    filename = os.path.splitext(filename)[0]
    return f"//{filename}_output"

def combine_to_output(row_count: int, column_count: int,
                      indexed_nodes: dict, background_node, output_name: str,
                      slice: bool = True):
    output_path = get_ouptut_path()
    context = bpy.context
    tree = context.scene.node_tree

    previous_result = background_node

    for r, c in indexed_nodes:
        rlnode = indexed_nodes[(r, c)]

        combined_background_node = tree.nodes.new('CompositorNodeAlphaOver')
        tree.links.new(background_node.outputs[0], combined_background_node.inputs[1])
        tree.links.new(rlnode.outputs[0], combined_background_node.inputs[2])

        tlnode = tree.nodes.new('CompositorNodeTranslate')
        iw, ih = single_render_dimensions()
        x_delta = -(iw * (column_count / 2 - 0.5)) + iw * c 
        y_delta = -(ih * (row_count / 2 - 0.5)) + ih * (row_count - 1 - r)
        tlnode.inputs[1].default_value = x_delta
        tlnode.inputs[2].default_value = y_delta
        tree.links.new(combined_background_node.outputs[0], tlnode.inputs[0])

        aonode = tree.nodes.new('CompositorNodeAlphaOver')    
        tree.links.new(previous_result.outputs[0], aonode.inputs[1])
        tree.links.new(tlnode.outputs[0], aonode.inputs[2])
        previous_result = aonode


    with_bg = tree.nodes.new('CompositorNodeAlphaOver')
    rgb = tree.nodes.new('CompositorNodeRGB')
    rgb.outputs[0].default_value = 0.918, 0.903, 0.704, 1

    tree.links.new(rgb.outputs[0], with_bg.inputs[1])
    tree.links.new(previous_result.outputs[0], with_bg.inputs[2])

    if slice:
        for r in range(0, row_count):
            left_crop_node = tree.nodes.new('CompositorNodeCrop')
            left_crop_node.relative = True
            left_crop_node.use_crop_size = True
            left_crop_node.rel_min_x = 0
            left_crop_node.rel_max_x = (column_count / 2 + 0.5) / column_count
            left_crop_node.rel_min_y = (row_count - 1 - r) / row_count
            left_crop_node.rel_max_y = ((row_count - 1 - r) + 1) / row_count

            right_crop_node = tree.nodes.new('CompositorNodeCrop')
            right_crop_node.relative = True
            right_crop_node.use_crop_size = True
            right_crop_node.rel_min_x = (column_count / 2 - 0.5) / column_count 
            right_crop_node.rel_max_x = 1
            right_crop_node.rel_min_y = (row_count - 1 - r) / row_count
            right_crop_node.rel_max_y = ((row_count - 1 - r) + 1) / row_count

            angle = r / (row_count - 1) * 180 + -90
            lofnode = tree.nodes.new('CompositorNodeOutputFile')
            lofnode.base_path = output_path
            lofnode.file_slots[0].path = f"{output_name}_left_{angle:+.01f}_"
            rofnode = tree.nodes.new('CompositorNodeOutputFile')
            rofnode.base_path = output_path
            rofnode.file_slots[0].path = f"{output_name}_right_{angle:+.01f}_"

            tree.links.new(with_bg.outputs[0], left_crop_node.inputs[0])
            tree.links.new(with_bg.outputs[0], right_crop_node.inputs[0])
            tree.links.new(left_crop_node.outputs[0], lofnode.inputs[0])
            tree.links.new(right_crop_node.outputs[0], rofnode.inputs[0])

    ofnode = tree.nodes.new('CompositorNodeOutputFile')
    ofnode.base_path = output_path
    ofnode.file_slots[0].path = f"{output_name}_"
    tree.links.new(with_bg.outputs[0], ofnode.inputs[0])


def generate_render_layers(parallel_count: int = 9, meridian_count: int = 16):
    context = bpy.context
    tree = context.scene.node_tree

    row_count = parallel_count
    column_count = meridian_count / 2 + 1 

    bgnode = generate_background_node(row_count, column_count)

    front_nodes = dict()
    back_nodes = dict()

    for vl in context.scene.view_layers:
        theta, phi = utils.parse_angles(vl.name)
        if math.isnan(theta):
            continue

        rlnode = tree.nodes.new('CompositorNodeRLayers')
        rlnode.layer = vl.name
        rlnode.scene = context.scene
        rlnode.show_preview = True
        # Very crude calculation. The width of a node is ~240
        rlnode.location = theta * 15, phi * -20

        r = int(round((phi + 90) / 180 * (row_count - 1)))
        if utils.greater_or_close(theta, 90) and utils.less_or_close(theta, 270):
            c = int(round((theta - 90) / 180 * (column_count - 1)))
            back_nodes[(r, c)] = rlnode
        # 90 & 270 degree appear on both. It's intentional
        if utils.less_or_close(theta, 90) or utils.greater_or_close(theta, 270):
            t = theta if utils.less_or_close(theta, 90) else theta - 360
            c = int(round((t - -90) / 180 * (column_count - 1)))
            front_nodes[(r, c)] = rlnode

    combine_to_output(row_count, column_count, front_nodes, bgnode, "front")
    combine_to_output(row_count, column_count, back_nodes, bgnode, "back")

    # Generate the special "subject" views
    subject_bg_node = generate_background_node(1, 5)
    center_row = row_count // 2
    center_column = column_count // 2
    top_rlnode = front_nodes[(row_count-1, center_column)]
    front_rlnode = front_nodes[(center_row, center_column)]
    right_rlnode = front_nodes[(center_row, 0)]
    # A little hacky way to get the indices of 3/4 views
    camera1_rlnode = front_nodes[(center_row+1, center_column*5//4)]
    camera2_rlnode = back_nodes[(center_row-1, center_column*7//4)]
    subject_nodes = {
        (0, 0): top_rlnode,
        (0, 1): front_rlnode,
        (0, 2): right_rlnode,
        (0, 3): camera1_rlnode,
        (0, 4): camera2_rlnode
    }

    combine_to_output(1, 5, subject_nodes, subject_bg_node, "subject", slice=False)



            
