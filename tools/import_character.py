"""Run inside Blender to study a USER-SUPPLIED rest face, never avatar visemes.

blender --background --factory-startup --disable-autoexec --python \
  tools/import_character.py -- /path/to/model.blend --settings local/character-settings.json

Produces private orthographic emission masks. No third-party mesh, texture or
shape-key data belongs in the repository. Follow with compile_character.py.
"""
import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model', type=Path)
    parser.add_argument('--output', type=Path, default=Path('local/character-source'))
    parser.add_argument('--settings', type=Path, required=True,
                        help='Private mesh, emission and projection settings; never commit this file')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(args.model.resolve()), use_scripts=False)
    settings = json.loads(args.settings.read_text())
    obj = bpy.data.objects[settings['mesh']]
    # Deliberately ignore every authored animation key, including visemes.
    if obj.data.shape_keys:
        for key in list(obj.data.shape_keys.key_blocks)[1:]:
            key.value = 0
        obj.data.shape_keys.animation_data_clear()
    for item in bpy.data.objects:
        item.hide_render = item != obj
    for collection in bpy.data.collections:
        collection.hide_render = False
    obj.hide_set(False)

    image = next(image for image in bpy.data.images
                 if settings['emission_image'] in image.name)
    for index in range(len(obj.data.materials)):
        name = str(index)
        material = bpy.data.materials.new('ProotfaceRest'+name)
        material.use_nodes = True
        nodes = material.node_tree.nodes
        nodes.clear()
        output = nodes.new('ShaderNodeOutputMaterial')
        emission = nodes.new('ShaderNodeEmission')
        emission.inputs['Color'].default_value = (0, 0, 0, 1)
        material.node_tree.links.new(emission.outputs[0], output.inputs[0])
        if index == settings['emission_material']:
            texture = nodes.new('ShaderNodeTexImage')
            texture.image = image
            material.node_tree.links.new(texture.outputs['Color'], emission.inputs['Color'])
        obj.data.materials[index] = material

    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 4
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 1536
    scene.render.resolution_y = 864
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.world = bpy.data.worlds.new('ProotfaceBlackWorld')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0,0,0,1)
    camera_data = bpy.data.cameras.new('ProotfaceRestCamera')
    camera = bpy.data.objects.new('ProotfaceRestCamera', camera_data)
    scene.collection.objects.link(camera)
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = settings['camera_width']
    scene.camera = camera
    left_sign = settings['anatomical_left_sign']
    for side, direction in (('left', left_sign), ('right', -left_sign)):
        target = Vector(settings['camera_center'])
        camera.location = target+Vector((settings.get('camera_distance',4*settings['camera_width'])*direction,0,0))
        camera.rotation_euler = (target-camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str((args.output/(side+'.png')).resolve())
        bpy.ops.render.render(write_still=True)
    print('Rest masks saved; no avatar animation keys exported.', flush=True)


if __name__ == '__main__':
    main()
