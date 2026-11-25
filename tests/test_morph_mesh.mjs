import test from 'node:test';
import assert from 'node:assert/strict';
import {blendVertices,buildMorphCharacter} from '../prootface/web/morph-character.mjs';

const rig={schema:2,positions:[0,0,.1,1,0,.1,0,1,.1],uvs:[0,0,1,0,0,1],
 parts:[{name:'surface',indices:[0,1,2],textured:true}],targets:{
 open:{indices:[1],deltas:[0,-1,0]},open_corrective:{indices:[1],deltas:[0,.3,0]}}};

test('sparse authored and corrective targets combine without changing source data',()=>{
 const original=[...rig.positions];
 const result=blendVertices(rig,{blend_open:.4,blend_open_corrective:.2});
 assert(Math.abs(result[4]+.34)<1e-6);
 assert.deepEqual(rig.positions,original);
});

test('full authored endpoint is preserved when corrective is zero',()=>{
 const result=blendVertices(rig,{blend_open:1,blend_open_corrective:0});
 assert.equal(result[4],-1);
 assert.equal(blendVertices(rig,{})[4],0);
});

test('opposite side projection changes depth sign and retains texture coordinates',()=>{
 const a=buildMorphCharacter(rig,{},'left').parts[0];
 const b=buildMorphCharacter(rig,{},'right').parts[0];
 assert.deepEqual(a.uvs,b.uvs);assert.equal(a.uvs.length,6);
 assert.equal(a.positions[2],-b.positions[2]);
 assert.equal(a.positions[0],b.positions[0]);assert(a.textured&&b.textured);
});

test('front restraint follows authored motion locally and preserves rear and expressions',()=>{
 const shape={positions:[0,0,0,.2,0,0,1,0,0],uvs:[0,0,0,0,0,0],parts:[],targets:{
  open:{indices:[0,1,2],deltas:[1,-2,3,1,-2,3,1,-2,3]},
  smile_left:{indices:[0],deltas:[.2,.3,0]}}};
 const full=blendVertices(shape,{blend_open:1,front_motion_scale:1});
 const limited=blendVertices(shape,{blend_open:1,front_motion_scale:.8});
 for(let axis=0;axis<3;axis++)assert(Math.abs(limited[axis]-full[axis]*.8)<1e-6);
 assert.deepEqual(limited.slice(6),full.slice(6));
 assert.deepEqual(blendVertices(shape,{front_motion_scale:0}),new Float32Array(shape.positions));
 assert.deepEqual(blendVertices(shape,{blend_smile_left:1,front_motion_scale:0}),
                  blendVertices(shape,{blend_smile_left:1,front_motion_scale:1}));
});
