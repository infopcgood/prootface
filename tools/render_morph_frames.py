"""Render private compiled morph data with exactly the same weights as WebGL."""
import argparse
import json
from pathlib import Path
import sys

import bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from prootface.rig import FRONT_TARGETS,front_motion_weights


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--character',type=Path,required=True)
    parser.add_argument('--poses',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.output.mkdir(parents=True,exist_ok=True)
    rig=json.loads(args.character.read_text());frames=json.loads(args.poses.read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    base=np.asarray(rig['positions'],dtype=float).reshape(-1,3)
    uv=np.asarray(rig['uvs']).reshape(-1,2)
    targets={name:(np.asarray(t['indices'],dtype=np.intp),np.asarray(t['deltas']).reshape(-1,3)) for name,t in rig['targets'].items()}
    front=np.asarray(rig.get('front_weights',front_motion_weights(rig)))
    zoom=rig['view']['zoom'];ox,oy=rig['view']['offset'];aspect=960/540
    sign=-rig.get('anatomical_left_sign',1)
    def project(points):
        out=points.copy()
        out[:,0]=(points[:,0]/1.88*zoom+ox)*aspect
        out[:,1]=(points[:,1]+.14)/1.16*zoom+oy
        out[:,2]=points[:,2]*sign
        return out
    faces=[];materials=[]
    for part in rig['parts']:
        faces.extend(np.asarray(part['indices']).reshape(-1,3).tolist())
        materials.extend([int(part['textured'])]*(len(part['indices'])//3))
    mesh=bpy.data.meshes.new('CompiledFace');mesh.from_pydata(project(base).tolist(),[],faces);mesh.update()
    obj=bpy.data.objects.new('CompiledFace',mesh);bpy.context.collection.objects.link(obj)
    layer=mesh.uv_layers.new()
    for loop in mesh.loops:layer.data[loop.index].uv=uv[loop.vertex_index]
    image=bpy.data.images.load(str(args.character.with_suffix('.png').resolve()))
    for bright in (False,True):
        material=bpy.data.materials.new('Emission' if bright else 'Occluder');material.use_nodes=True
        nodes=material.node_tree.nodes;nodes.clear()
        output=nodes.new('ShaderNodeOutputMaterial');emission=nodes.new('ShaderNodeEmission')
        emission.inputs['Color'].default_value=(0,0,0,1)
        material.node_tree.links.new(emission.outputs[0],output.inputs[0])
        if bright:
            texture=nodes.new('ShaderNodeTexImage');texture.image=image
            material.node_tree.links.new(texture.outputs['Color'],emission.inputs['Color'])
        mesh.materials.append(material)
    for poly,index in zip(mesh.polygons,materials):poly.material_index=index
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=2
    scene.cycles.use_denoising=False
    scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    scene.world=bpy.data.worlds.new('Black');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(0,0,0,1)
    camera_data=bpy.data.cameras.new('ReviewCamera');camera=bpy.data.objects.new('ReviewCamera',camera_data)
    scene.collection.objects.link(camera);camera.location=(0,0,10)
    camera.rotation_euler=(Vector((0,0,0))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera_data.type='ORTHO';camera_data.ortho_scale=2*aspect;scene.camera=camera
    for index,pose in enumerate(frames):
        points=base.copy()
        for semantic,(indices,deltas) in targets.items():
            weight=max(0,min(1,pose.get('blend_'+semantic,0)))
            if weight:
                local=(1-(1-pose.get('front_motion_scale',1))*front[indices]) if semantic in FRONT_TARGETS else np.ones(len(indices))
                points[indices]+=weight*deltas*local[:,None]
        mesh.vertices.foreach_set('co',project(points).ravel());mesh.update()
        scene.render.filepath=str((args.output/f'{index:05}.png').resolve())
        bpy.ops.render.render(write_still=True)
        if index%15==0:print('REVIEW_FRAME',index,len(frames),flush=True)
    print('MORPH_REVIEW_RENDER_COMPLETE',flush=True)


if __name__=='__main__':main()
