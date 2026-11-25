import test from 'node:test';
import assert from 'node:assert/strict';
import {buildMouth,profileAt,REST,DEFAULT_STYLE,sampleLedMap} from '../prootface/web/mouth.mjs';

test('contact coincides around the entire contour, including the attached V',()=>{
 const p={...REST,opening:1,seal:1,aperture:0,jaw_angle:.36};
 for(let i=0;i<=1000;i++){
  const {upper,lower}=profileAt(p,DEFAULT_STYLE,i/1000);
  assert.deepEqual(lower,upper);
 }
});

test('one V point is built into the lip boundary and has exact roots/tip',()=>{
 const s=DEFAULT_STYLE,m=buildMouth(REST);
 for(const t of [s.v_position-s.v_width,s.v_position,s.v_position+s.v_width])
  assert(m.samples.some(q=>Math.abs(q.t-t)<1e-10));
 assert.equal(m.parts.filter(p=>/tooth|tongue|fang/.test(p.name)).length,0);
 const tip=profileAt(REST,s,s.v_position);
 assert(Math.abs(tip.tooth-s.v_depth)<1e-10);
 for(const t of [s.v_position-s.v_width,s.v_position+s.v_width])
  assert(profileAt(REST,s,t).tooth<1e-10);
});

test('mixed poses remain finite and lip contours do not cross',()=>{
 for(const aperture of [0,.01,.1,.4,1])for(const rounding of [0,.5,1])for(const corner of [-1,0,1]){
  const p={...REST,aperture,opening:aperture,seal:aperture?0:1,jaw_angle:.36*aperture,
   jaw_recession:.12*aperture,width_scale:1-.28*rounding,rounding,corner_right_render:corner};
  const model=buildMouth(p);
  for(const q of model.samples)assert(q.lower[1]<=q.upper[1]+1e-8);
  for(const part of model.parts)assert(part.positions.every(Number.isFinite));
 }
});

test('front and rear return to contact rather than forming the rejected wedge',()=>{
 const p={...REST,aperture:.7,seal:0,jaw_angle:.25,jaw_recession:.08};
 for(const t of [0,1]){
  const {upper,lower}=profileAt(p,DEFAULT_STYLE,t);
  assert(Math.abs(upper[1]-lower[1])<1e-8);
 }
 const mid=profileAt(p,DEFAULT_STYLE,.35);
 assert(mid.lower[1]<mid.upper[1]-.15);
 assert(mid.lower[0]>mid.upper[0]);
});

test('shared symmetric inputs make matching anatomical surfaces',()=>{
 const p={...REST,aperture:.5,seal:0,jaw_angle:.18,corner_left_render:.4,corner_right_render:.4};
 const a=buildMouth(p,{},'left'),b=buildMouth(p,{},'right');
 assert.deepEqual(a.samples,b.samples);
});

test('LED map samples top-left UV from bottom-left framebuffer without swapping RGB',()=>{
 const rgba=new Uint8Array([255,0,0,255,0,255,0,255,0,0,255,255,255,255,255,255]);
 assert.deepEqual(sampleLedMap(rgba,2,2,[{u:0,v:0},{u:1,v:1},{u:.5,v:.5}]),[[0,0,255],[0,255,0],[128,128,128]]);
 assert.throws(()=>sampleLedMap(rgba,2,2,[{u:2,v:0}]));
});
