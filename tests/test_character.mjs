import test from 'node:test';
import assert from 'node:assert/strict';
import {buildCharacter,deformPart,signedArea,triangulate} from '../prootface/web/character.mjs';
import {REST} from '../prootface/web/mouth.mjs';

// Original synthetic concave ribbon, not vertices from the supplied avatar.
const mouth={name:'mouth',points:[[-1,.1,0,0],[.3,.4,.65,0],[.9,.25,1,0],
 [.4,.15,.75,.25],[.15,-.2,.575,1],[-1,-.05,0,1]]};
const character={schema:1,sides:{left:{parts:[mouth]},right:{parts:[mouth]}}};
const almost=(a,b)=>assert(Math.abs(a-b)<1e-10);

test('neutral and closed conflicting opening preserve the source ribbon',()=>{
 for(const pose of [REST,{...REST,seal:1,aperture:1}]){
  const points=deformPart(mouth,pose);
  points.forEach((p,i)=>{almost(p[0],mouth.points[i][0]);almost(p[1],mouth.points[i][1]);});
 }
});

test('concave outlines triangulate with the same covered area',()=>{
 const points=mouth.points.map(p=>p.slice(0,2)),indices=triangulate(points);
 assert.equal(indices.length,(points.length-2)*3);
 let area=0;
 for(let i=0;i<indices.length;i+=3)area+=Math.abs(signedArea(indices.slice(i,i+3).map(j=>points[j])));
 almost(area,Math.abs(signedArea(points)));
});

test('mouth expansion recedes, preserves corners and remains finite in mixed poses',()=>{
 for(const a of [0,.1,.5,1])for(const r of [0,.5,1])for(const c of [-1,0,1]){
  const p={...REST,seal:a?0:1,aperture:a,rounding:r,width_scale:1-.28*r,
   corner_left_render:c,corner_right_render:c};
  const mesh=buildCharacter(character,p);
  assert(mesh.parts[0].positions.every(Number.isFinite));
 }
 const open=deformPart(mouth,{...REST,seal:0,aperture:.6});
 assert(open[4][0]>mouth.points[4][0]);
 assert(open[4][1]<mouth.points[4][1]);
 const rounded=deformPart(mouth,{...REST,rounding:1,width_scale:.72,corner_right_render:.5});
 assert(rounded[2][1]>mouth.points[2][1]);
});

test('one shared symmetric pose makes equal anatomical deformations before projection',()=>{
 const p={...REST,seal:0,aperture:.5,corner_left_render:.2,corner_right_render:.2};
 assert.deepEqual(buildCharacter(character,p,{},'left').parts[0].outline,
                  buildCharacter(character,p,{},'right').parts[0].outline);
});
