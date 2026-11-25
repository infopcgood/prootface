// Original profile-surface study. Coordinates are artistic, NOT Sigma CAD dimensions.
// A shared pose deforms each anatomical side; mirror only the display projection.
export const clamp = (x, a=0, b=1) => Math.max(a, Math.min(b, x));
const mix = (a,b,t) => a+(b-a)*t;
const smooth = (a,b,x) => { const t=clamp((x-a)/(b-a)); return t*t*(3-2*t); };
export const DEFAULT_STYLE = {max_jaw_angle:.36,recession:.12,opening_gamma:.85,
  max_corner_lift:.20,asymmetry:.7,v_depth:.11,v_position:.88,v_width:.045,lip_thickness:.016};
export const REST = {opening:0,aperture:0,rounding:0,spread:0,seal:1,tension:0,
  jaw_angle:0,jaw_recession:0,width_scale:1,corner_left:0,corner_right:0,
  corner_left_render:0,corner_right_render:0,eye_left:1,eye_right:1,brow_left:0,brow_right:0};

export function profileAt(pose, style, t, side='right') {
  const p={...REST,...pose}, s={...DEFAULT_STYLE,...style};
  const corner=p[`corner_${side}_render`] ?? p[`corner_${side}`];
  const lift=s.max_corner_lift*corner;
  const width=clamp(p.width_scale,.65,1.1);
  const hinge=1.31 + .06*p.spread;
  const x=hinge - 2.72*width*(1-t);
  const baseline=.025+.045*Math.sin(Math.PI*t)+lift*smooth(.45,1,t);
  // Exactly one attached posterior V. Its two roots and tip are in the lip mesh.
  const tooth=s.v_depth*Math.max(0,1-Math.abs(t-s.v_position)/s.v_width);
  const upper=[x,baseline-tooth,.13];
  const angle=clamp(p.jaw_angle,0,.65);
  // Art-directed jaw arc: round the front return into contact; retain a narrow
  // posterior corner. This avoids the rigid crocodile wedge rejected in v1.
  const frontReturn=Math.sin(Math.PI*t)**.82;
  const drop=1.65*Math.sin(angle)*frontReturn*(1-.12*t);
  const lowerRest=baseline-tooth*(1-smooth(.01,.20,p.aperture));
  let lower=[x+(hinge-x)*(1-Math.cos(angle))*frontReturn+
    p.jaw_recession*Math.sin(Math.PI*t),lowerRest-drop,.115];
  // Lip contact is a geometric constraint, including at the posterior V.
  lower[1]=Math.min(upper[1],lower[1]);
  if (p.seal>=.999 || p.aperture<1e-5) lower=[...upper];
  return {upper,lower,t,tooth};
}

class Mesh {
  constructor(name){this.name=name;this.positions=[];this.colors=[];}
  tri(a,b,c,ca,cb=ca,cc=ca){this.positions.push(...a,...b,...c);this.colors.push(...ca,...cb,...cc);}
  quad(a,b,c,d,ca,cb=ca,cc=ca,cd=ca){this.tri(a,b,c,ca,cb,cc);this.tri(a,c,d,ca,cc,cd);}
  finish(){
    const normals=[];
    for(let i=0;i<this.positions.length;i+=9){
      const v=this.positions, ax=v[i+3]-v[i],ay=v[i+4]-v[i+1],az=v[i+5]-v[i+2];
      const bx=v[i+6]-v[i],by=v[i+7]-v[i+1],bz=v[i+8]-v[i+2];
      let n=[ay*bz-az*by,az*bx-ax*bz,ax*by-ay*bx];
      const len=Math.hypot(...n)||1;n=n.map(x=>x/len);
      if(n[2]<0)n=n.map(x=>-x);
      normals.push(...n,...n,...n);
    }
    return {name:this.name,positions:new Float32Array(this.positions),
      colors:new Float32Array(this.colors),normals:new Float32Array(normals)};
  }
}

export function buildMouth(pose,style={},side='right') {
  const p={...REST,...pose},s={...DEFAULT_STYLE,...style};
  const ts=Array.from({length:81},(_,i)=>i/80);
  ts.push(s.v_position-s.v_width,s.v_position,s.v_position+s.v_width);
  const samples=[...new Set(ts.map(t=>clamp(t)))].sort((a,b)=>a-b).map(t=>profileAt(p,s,t,side));
  const cavity=new Mesh('cavity'),upper=new Mesh('upper-lip'),lower=new Mesh('lower-lip'),seam=new Mesh('contact-seam');
  const boundary=(q,isUpper,r)=>{
    const v=isUpper?q.upper:q.lower;
    const dir=isUpper?1:-1;
    const taper=.45+.55*Math.sin(Math.PI*q.t)**.35;
    const roll=s.lip_thickness*(1+.15*p.rounding);
    return [v[0],v[1]+dir*r*taper*roll,.13-r*.003];
  };
  const colors=r=>{
    // One clean contour with soft coverage. No glossy tubular/ridged flesh.
    return [.66,.84,.87,1-smooth(.72,1,r)];
  };
  for(let i=0;i<samples.length-1;i++){
    const a=samples[i],b=samples[i+1];
    // Concave shaded cavity. No tongue, gum geometry, tooth rows or detached fangs.
    for(let j=0;j<8;j++){
      const f=j/8,g=(j+1)/8;
      const point=(q,k)=>[mix(q.upper[0],q.lower[0],k),mix(q.upper[1],q.lower[1],k),
        .115-.53*Math.sin(Math.PI*k)*Math.sin(Math.PI*q.t)**.35];
      const col=k=>{const edge=Math.abs(k-.5)*2;return [.004+.024*edge,.010+.049*edge,.014+.053*edge,1];};
      cavity.quad(point(a,f),point(b,f),point(b,g),point(a,g),col(f),col(f),col(g),col(g));
    }
    for(let j=0;j<3;j++){
      const f=j/3,g=(j+1)/3;
      for(const [mesh,isUpper] of [[upper,true],[lower,false]]){
        mesh.quad(boundary(a,isUpper,f),boundary(b,isUpper,f),
          boundary(b,isUpper,g),boundary(a,isUpper,g),colors(f),colors(f),colors(g),colors(g));
      }
    }
  }
  // A restrained eye marker establishes the posterior/eye side of each study.
  const eye=new Mesh('eye');
  const eyeOpen=clamp(p[`eye_${side}`],.025,1),brow=p[`brow_${side}`]||0;
  const center=[.78,.68+brow*.06,.02];
  for(let i=0;i<48;i++){
    const point=k=>{const a=k/48*Math.PI*2;return [center[0]+.30*Math.cos(a),
      center[1]+.13*eyeOpen*Math.sin(a),.03];};
    eye.tri(center,point(i),point(i+1),[.55,.77,.80,.95]);
  }
  return {parts:[cavity,upper,lower,seam,eye].map(m=>m.finish()),samples};
}

// Schematic UV boundary informed by the WS35 reference image, not a traced CAD outline.
// Actual custom panel shape and LED map must be measured before deployment.
export const WS_STUDY_MASK=[[.035,.34],[.82,.065],[.965,.20],[.945,.91],[.12,.96],[.025,.62]];

export function sampleLedMap(rgba,width,height,coordinates){
  // Input UVs have top-left origin; WebGL readPixels has bottom-left origin.
  return coordinates.map(({u,v})=>{
    if(!Number.isFinite(u)||!Number.isFinite(v)||u<0||u>1||v<0||v>1)throw Error('LED UV out of range');
    const x=u*(width-1),y=(1-v)*(height-1),x0=Math.floor(x),y0=Math.floor(y);
    return [0,1,2].map(c=>{
      const at=(xx,yy)=>rgba[(Math.min(height-1,yy)*width+Math.min(width-1,xx))*4+c];
      return Math.round(mix(mix(at(x0,y0),at(x0+1,y0),x-x0),mix(at(x0,y0+1),at(x0+1,y0+1),x-x0),y-y0));
    });
  });
}

