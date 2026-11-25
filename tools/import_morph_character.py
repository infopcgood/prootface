"""Export a privately configured authored pose basis for two flat side views.

blender --background --factory-startup --disable-autoexec --python \
  tools/import_morph_character.py -- model.blend --settings local/settings.json \
  --output local/character.json

Private settings map semantic targets to source animation keys. Nothing from
the user's source file or settings belongs in the public repository.
"""
import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model',type=Path)
    parser.add_argument('--settings',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('local/character.json'))
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    settings=json.loads(args.settings.read_text())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(args.model.resolve()),use_scripts=False)
    obj=bpy.data.objects[settings['mesh']]
    keys=obj.data.shape_keys
    if not keys:raise ValueError('Configured mesh has no authored pose targets')
    keys.animation_data_clear()
    def reset():
        for key in list(keys.key_blocks)[1:]:key.value=0
        bpy.context.view_layer.update()
    reset()
    center=Vector(settings['camera_center']);width=settings['camera_width']
    sx,sy=3.76/width,2.32/(width*864/1536)
    def project(co):
        p=obj.matrix_world@co
        return [(p.y-center.y)*sx,(p.z-center.z)*sy-.14,(p.x-center.x)*sx]
    deps=bpy.context.evaluated_depsgraph_get()
    evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh()
    mesh.calc_loop_triangles()
    uv=mesh.uv_layers.active.data
    vertices=[];texcoords=[];original=[];unique={};groups={False:[],True:[]}
    emission=settings['emission_material']
    for triangle in mesh.loop_triangles:
        bright=mesh.polygons[triangle.polygon_index].material_index==emission
        for loop_index in triangle.loops:
            vertex=mesh.loops[loop_index].vertex_index
            coord=list(uv[loop_index].uv)
            key=(vertex,round(coord[0],7),round(coord[1],7),bright)
            if key not in unique:
                unique[key]=len(original);original.append(vertex)
                vertices.extend(project(mesh.vertices[vertex].co));texcoords.extend(coord)
            groups[bright].append(unique[key])
    base=[Vector(v.co) for v in mesh.vertices]
    evaluated.to_mesh_clear()
    targets={}
    for semantic,mapping in settings['targets'].items():
        reset()
        for name,value in mapping.items():keys.key_blocks[name].value=value
        bpy.context.view_layer.update()
        evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());posed=evaluated.to_mesh()
        if len(posed.vertices)!=len(base):raise ValueError('Target changes mesh topology')
        indices=[];deltas=[]
        for i,source in enumerate(original):
            a=project(posed.vertices[source].co);b=vertices[i*3:i*3+3]
            delta=[a[k]-b[k] for k in range(3)]
            if max(abs(v) for v in delta)>1e-7:
                indices.append(i);deltas.extend(round(v,8) for v in delta)
        targets[semantic]=dict(indices=indices,deltas=deltas)
        evaluated.to_mesh_clear()
    reset()
    # Bound all authored mouth samples once. The camera never zooms per frame.
    # Include a fixed margin for the smaller additive expression adjustments.
    bright=set(groups[True]);bounds=[]
    for i in bright:bounds.append(vertices[3*i:3*i+2])
    for name in ('open','round','wide','closed','bite','sibilant','postalveolar','rhotic'):
        target=targets.get(name,{})
        for j,i in enumerate(target.get('indices',[])):
            if i in bright:bounds.append([vertices[3*i]+target['deltas'][3*j],
                                         vertices[3*i+1]+target['deltas'][3*j+1]])
    xmin=min(p[0] for p in bounds);xmax=max(p[0] for p in bounds)
    ymin=min(p[1] for p in bounds);ymax=max(p[1] for p in bounds)
    zoom=min(3.35/(xmax-xmin),1.98/(ymax-ymin))
    view=dict(zoom=zoom,offset=[-(xmin+xmax)/2/1.88*zoom,-((ymin+ymax)/2+.14)/1.16*zoom])
    data=dict(schema=2,kind='authored_morph_mesh',
              positions=[round(v,8) for v in vertices],uvs=[round(v,8) for v in texcoords],
              parts=[dict(name='occluder',indices=groups[False],textured=False),
                     dict(name='emission',indices=groups[True],textured=True)],
              targets=targets,view=view,anatomical_left_sign=settings['anatomical_left_sign'])
    args.output.write_text(json.dumps(data,separators=(',',':'))+'\n')
    image=next(image for image in bpy.data.images if settings['emission_image'] in image.name)
    if image.packed_file:args.output.with_suffix('.png').write_bytes(image.packed_file.data)
    else:image.save_render(str(args.output.with_suffix('.png').resolve()))
    print('Exported privately configured morph rig:',len(original),'vertices;',len(targets),'semantic targets',flush=True)


if __name__=='__main__':main()
