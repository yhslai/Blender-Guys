import importlib
import cameraman
import compositorman

importlib.reload(cameraman)
importlib.reload(compositorman)

PARALLEL_COUNT = 9
MERIDIAN_COUNT = 16

def execute():
    # cameraman.prepare_view_layer()
    # cameraman.generate_multi_view_layer(PARALLEL_COUNT, MERIDIAN_COUNT)
    compositorman.prepare_compositor()
    compositorman.generate_render_layers(PARALLEL_COUNT, MERIDIAN_COUNT)