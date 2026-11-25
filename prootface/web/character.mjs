// Procedural motion of a USER-SUPPLIED rest silhouette. No avatar viseme keys.
import {clamp,DEFAULT_STYLE,REST} from './mouth.mjs';
import {buildMorphCharacter} from './morph-character.mjs';
const ease=x=>{x=clamp(x);return x*x*(3-2*x);};
const cross=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
export const signedArea=points=>points.reduce((a,p,i)=>{
 const q=points[(i+1)%points.length];return a+p[0]*q[1]-p[1]*q[0];
},0)/2;

export function triangulate(points){
 const remaining=points.map((_,i)=>i),triangles=[];
 if(signedArea(points)<0)remaining.reverse();
 let attempts=0;
 while(remaining.length>3){
  let found=false;
  for(let i=0;i<remaining.length;i++){
   const a=remaining[(i+remaining.length-1)%remaining.length],b=remaining[i],c=remaining[(i+1)%remaining.length];
   if(cross(points[a],points[b],points[c])<=1e-10)continue;
   const occupied=remaining.some(k=>k!==a&&k!==b&&k!==c&&
    cross(points[a],points[b],points[k])>=-1e-10&&
    cross(points[b],points[c],points[k])>=-1e-10&&
    cross(points[c],points[a],points[k])>=-1e-10);
   if(occupied)continue;
   triangles.push(a,b,c);remaining.splice(i,1);found=true;break;
  }
  if(!found||++attempts>points.length)throw Error('Character outline cannot be triangulated safely');
 }
 triangles.push(...remaining);return triangles;
}

export function deformPart(part,pose,style={},side='right'){
 const p={...REST,...pose},s={...DEFAULT_STYLE,...style};
 const xs=part.points.map(q=>q[0]),ys=part.points.map(q=>q[1]);
 const front=Math.min(...xs),rear=Math.max(...xs),span=rear-front;
 const centerY=(Math.min(...ys)+Math.max(...ys))/2;
 const corner=p[`corner_${side}_render`]??0;
 // Contact suppresses opening after all other controls, including noisy jaw input.
 const aperture=p.seal>=.999?0:clamp(p.aperture);
 return part.points.map(([x,y,t,lower])=>{
  if(part.name==='mouth'){
   const envelope=Math.sin(Math.PI*clamp(t))**.72;
   const round=clamp(p.rounding),width=clamp(p.width_scale,.72,1.10);
   const drop=span*.32*aperture*envelope*(s.max_jaw_angle/.36)*(1+.18*round);
   const recession=span*.09*aperture*envelope*lower*(s.recession/.12);
   const lift=span*.16*corner*ease((t-.30)/.70)*(s.max_corner_lift/.20);
   // Monotonic vertical expansion retains the source's notch and hooked return.
   // Upper lip leads; the lower ribbon swings down and back. No tubular lip mesh.
   return [rear+(x-rear)*width+recession,
    y-drop*lower+lift+span*.025*round*aperture*envelope*(1-lower)];
  }
  if(part.name==='eye'){
   const eye=clamp(p[`eye_${side}`],.035,1);
   const cheek=Math.max(0,corner)*.035;
   return [x,centerY+(y-centerY)*eye+cheek];
  }
  return [x,y];
 });
}

export function buildCharacter(character,pose,style={},side='right'){
 if(character.schema===2)return buildMorphCharacter(character,pose,side);
 if(character.schema!==1||!character.sides?.[side])throw Error('Unsupported character data');
 const source=character.sides[side],color=character.color??[.2,.8,1,1];
 const parts=source.parts.map(part=>{
  const outline=deformPart(part,pose,style,side),indices=triangulate(outline);
  const positions=[],normals=[],colors=[];
  for(const i of indices){positions.push(...outline[i],.1);normals.push(0,0,1);colors.push(...color);}
  return {name:part.name,outline,unlit:true,positions:new Float32Array(positions),
   normals:new Float32Array(normals),colors:new Float32Array(colors)};
 });
 return {parts};
}
