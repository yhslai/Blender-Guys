import bpy

def copy_from_main_layer(name = "Copy"):
    context = bpy.context
    old_layer = context.scene.view_layers["Main"]
    new_layer = context.scene.view_layers.new(name)
    collection = old_layer.layer_collection
    new_collection = new_layer.layer_collection

    for prop in dir(new_layer):
        try:
            attr = getattr(old_layer,prop)
            setattr(new_layer, prop, attr)
        except:
            pass
    
    new_layer.name = name

    cycles = old_layer.cycles
    new_cycles = new_layer.cycles
    for prop in dir(new_cycles):
        try:
            attr = getattr(cycles,prop)
            setattr(new_cycles, prop, attr)
        except:
            pass

    for linesetsFrom in old_layer.freestyle_settings.linesets:
        linesetsTo = new_layer.freestyle_settings.linesets.new(linesetsFrom.name)

        excludes = ('__doc__', '__module__', '__slots__', 'bl_rna', 'rna_type')

        for name in dir(linesetsFrom):
            attr = getattr(linesetsFrom, name)
            if name not in excludes:
                try:
                    setattr(linesetsTo, name, attr)
                except:
                    pass

    def recursive_attributes(collection, new_collection):
        new_collection.exclude = collection.exclude
        new_collection.holdout = collection.holdout
        new_collection.indirect_only = collection.indirect_only
        new_collection.hide_viewport = collection.hide_viewport

        for i, _ in enumerate(new_collection.children):
            old_child = collection.children[i]
            new_child = new_collection.children[i]
            recursive_attributes(old_child, new_child)

        for i, _ in enumerate(new_collection.collection.objects):
            tmp = collection.collection.objects[i].hide_get()
            new_collection.collection.objects[i].hide_set(tmp)

        return 0

    recursive_attributes(collection, new_collection)
    context.window.view_layer = new_layer

    return new_layer