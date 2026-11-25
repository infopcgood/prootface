import {buildMouth,WS_STUDY_MASK} from './mouth.mjs';

const VS=`
attribute vec3 position;attribute vec3 normal;attribute vec4 color;
uniform float mirror;uniform float yaw;uniform float zoom;uniform vec2 offset;
varying vec3 vNormal;varying vec3 vPosition;varying vec4 vColor;varying vec2 vUV;
void main(){
 float c=cos(yaw),s=sin(yaw);mat3 rot=mat3(c,0.,-s,0.,1.,0.,s,0.,c);
 vec3 p=rot*position;vNormal=rot*normal;vPosition=p;vColor=color;
 vec2 clip=vec2(p.x/1.88,(p.y+.14)/1.16)*zoom+offset;
 vUV=vec2(clip.x*.5+.5,.5-clip.y*.5);
 gl_Position=vec4(clip.x*mirror,clip.y,-p.z*.25,1.);
}`;
const FS=`
precision mediump float;
uniform bool maskEnabled;uniform vec2 polygon[6];uniform float grid;
varying vec3 vNormal;varying vec3 vPosition;varying vec4 vColor;varying vec2 vUV;
bool crosses(vec2 p,vec2 a,vec2 b){return (a.y>p.y)!=(b.y>p.y)&&p.x<(b.x-a.x)*(p.y-a.y)/(b.y-a.y)+a.x;}
bool inside(vec2 p){bool v=crosses(p,polygon[0],polygon[5]);
 v=v!=crosses(p,polygon[1],polygon[0]);v=v!=crosses(p,polygon[2],polygon[1]);
 v=v!=crosses(p,polygon[3],polygon[2]);v=v!=crosses(p,polygon[4],polygon[3]);
 return v!=crosses(p,polygon[5],polygon[4]);}
void main(){
 if(maskEnabled&&!inside(vUV))discard;
 if(vColor.a<.005)discard;
 // Mirroring a display reverses winding; it must not reverse its lighting.
 vec3 n=normalize(vNormal);if(n.z<0.)n=-n;
 vec3 light=normalize(vec3(-.4,.8,1.3));
 float diffuse=.32+.68*max(0.,dot(n,light));
 float shine=0.;
 vec3 rgb=vColor.rgb*diffuse+vec3(shine)*min(1.,length(vColor.rgb)*2.);
 if(grid>0.){vec2 g=fract(vUV*vec2(grid,grid*.56));float dotMask=1.-smoothstep(.32,.48,length(g-.5));rgb*=.25+.75*dotMask;}
 gl_FragColor=vec4(rgb,vColor.a);
}`;

export class Renderer{
 constructor(canvas,side){
  this.canvas=canvas;this.side=side;this.options={mask:true,grid:0,yaw:0,zoom:1,offset:[0,0]};
  const gl=canvas.getContext('webgl',{antialias:true,alpha:false,preserveDrawingBuffer:true});
  if(!gl)throw Error('WebGL is required for the dimensional mouth preview');this.gl=gl;
  const shader=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);
    if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
  this.program=gl.createProgram();gl.attachShader(this.program,shader(gl.VERTEX_SHADER,VS));
  gl.attachShader(this.program,shader(gl.FRAGMENT_SHADER,FS));gl.linkProgram(this.program);
  if(!gl.getProgramParameter(this.program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(this.program));
  this.buffers=['position','normal','color'].map(name=>({name,buffer:gl.createBuffer(),loc:gl.getAttribLocation(this.program,name)}));
  this.uniforms=Object.fromEntries(['mirror','yaw','zoom','offset','maskEnabled','polygon[0]','grid'].map(k=>[k,gl.getUniformLocation(this.program,k)]));
  gl.enable(gl.DEPTH_TEST);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
 }
 draw(pose,style){
  const gl=this.gl,c=this.canvas;const dpr=Math.min(2,window.devicePixelRatio||1);
  const width=Math.round(c.clientWidth*dpr),height=Math.round(c.clientHeight*dpr);
  if(c.width!==width||c.height!==height){c.width=width;c.height=height;}
  gl.viewport(0,0,c.width,c.height);gl.clearColor(0,0,0,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.useProgram(this.program);
  const u=this.uniforms,o=this.options;
  gl.uniform1f(u.mirror,this.side==='left'?-1:1);gl.uniform1f(u.yaw,o.yaw);gl.uniform1f(u.zoom,o.zoom);
  gl.uniform2fv(u.offset,o.offset);gl.uniform1i(u.maskEnabled,o.mask);gl.uniform1f(u.grid,o.grid);
  gl.uniform2fv(u['polygon[0]'],WS_STUDY_MASK.flat());
  const mesh=buildMouth(pose,style,this.side);this.lastMesh=mesh;
  for(const part of mesh.parts){
   for(const [i,key] of ['positions','normals','colors'].entries()){
    const b=this.buffers[i];gl.bindBuffer(gl.ARRAY_BUFFER,b.buffer);gl.bufferData(gl.ARRAY_BUFFER,part[key],gl.DYNAMIC_DRAW);
    gl.enableVertexAttribArray(b.loc);gl.vertexAttribPointer(b.loc,i===2?4:3,gl.FLOAT,false,0,0);
   }
   gl.drawArrays(gl.TRIANGLES,0,part.positions.length/3);
  }
 }
}

