// Generic authored-mesh blendspace. Private source targets remain external data.
const cached=new WeakMap();
const frontTargets=new Set(['open','round','wide','bite','sibilant','postalveolar','rhotic']);
function frontWeights(character){
 if(character.front_weights)return new Float32Array(character.front_weights);
 const count=character.positions.length/3,weights=new Float32Array(count);
 const indices=new Set(['open','round','wide'].flatMap(name=>character.targets[name]?.indices??[]));
 if(!indices.size)return weights;
 const xs=[...indices].map(i=>character.positions[i*3]),front=Math.min(...xs),rear=Math.max(...xs);
 if(rear-front<1e-8)return weights;
 for(let i=0;i<count;i++){
  const t=(character.positions[i*3]-front)/(rear-front),u=Math.max(0,Math.min(1,(t-.10)/.25));
  weights[i]=1-u*u*(3-2*u);
 }
 return weights;
}
function prepare(character){
 if(cached.has(character))return cached.get(character);
 const value={base:new Float32Array(character.positions),uv:new Float32Array(character.uvs),front:frontWeights(character),
  frontTargets:new Set([...frontTargets,...(character.front_targets??[])]),
  targets:Object.fromEntries(Object.entries(character.targets).map(([name,t])=>[name,
   {indices:new Uint32Array(t.indices),deltas:new Float32Array(t.deltas)}]))};
 cached.set(character,value);return value;
}

export function blendVertices(character,pose){
 const data=prepare(character),positions=new Float32Array(data.base);
 const frontScale=Math.max(0,Math.min(1,pose.front_motion_scale??1));
 for(const [name,target] of Object.entries(data.targets)){
  const weight=Math.max(0,Math.min(1,pose['blend_'+name]??0));
  if(weight<1e-7)continue;
  for(let j=0;j<target.indices.length;j++){
   const i=target.indices[j]*3;
   const local=data.frontTargets.has(name)?1-(1-frontScale)*data.front[target.indices[j]]:1;
   positions[i]+=weight*local*target.deltas[j*3];
   positions[i+1]+=weight*local*target.deltas[j*3+1];
   positions[i+2]+=weight*local*target.deltas[j*3+2];
  }
 }
 return positions;
}

export function buildMorphCharacter(character,pose,side='right'){
 const data=prepare(character),vertices=blendVertices(character,pose);
 const sign=(character.anatomical_left_sign??1)*(side==='left'?1:-1);
 const parts=character.parts.map(part=>{
  const count=part.indices.length,positions=new Float32Array(count*3),normals=new Float32Array(count*3),
   colors=new Float32Array(count*4),uvs=new Float32Array(count*2);
  part.indices.forEach((vertex,j)=>{
   const i=vertex*3;positions.set([vertices[i],vertices[i+1],vertices[i+2]*sign],j*3);
   normals.set([0,0,1],j*3);colors.set(part.textured?[1,1,1,1]:[0,0,0,1],j*4);
   uvs.set(data.uv.subarray(vertex*2,vertex*2+2),j*2);
  });
  return {name:part.name,positions,normals,colors,uvs,unlit:true,textured:part.textured};
 });
 return {parts};
}
