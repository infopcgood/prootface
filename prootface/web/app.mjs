import {Renderer} from './renderer.mjs';
import {REST} from './mouth.mjs';

const $=s=>document.querySelector(s), params=new URLSearchParams(location.search);
const only=params.get('side');if(params.get('display')==='1')document.body.classList.add('output');
let character=null;
try{const response=await fetch('/api/character');if(response.ok)character=await response.json();}catch{}
const renderers=['left','right'].filter(side=>!only||only===side).map(side=>new Renderer($('#'+side),side,character));
if(character){$('footer').textContent=character.schema===2?'24 fps · authored pose basis · causal live controller':'Legacy rest-silhouette study';}
else{$('footer').textContent='Character asset not loaded · showing the original contour study';}
if(only)document.querySelectorAll('figure').forEach(f=>{if(f.querySelector('canvas').id!==only)f.remove();});
let state={pose:REST,style:{}},current={...REST},lastSequence=-1,lastRendered=-1;
async function post(path,data={}){
 try{const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
 const result=await response.json();if(!response.ok)throw Error(result.error);$('#error').textContent='';return result;
 }catch(e){$('#error').textContent=e.message;}
}

function slider(parent,key,label,min,max,value,onChange){
 const wrapper=document.createElement('label');wrapper.className='control';wrapper.textContent=label;
 const output=document.createElement('output');output.textContent=value.toFixed(2);wrapper.append(output);
 const input=document.createElement('input');Object.assign(input,{type:'range',min,max,step:.01,value});input.dataset.key=key;
 input.oninput=()=>{output.textContent=Number(input.value).toFixed(2);onChange(key,Number(input.value));};wrapper.append(input);parent.append(wrapper);
}
const controls=[['opening','Jaw opening',0,1,0],['rounding','Rounding',0,1,0],['spread','Spreading',0,1,0],
 ['seal','Lip contact',0,1,1],['corner_left','Left corner',-1,1,0],['corner_right','Right corner',-1,1,0]];
for(const [key,label,min,max,value] of controls)slider($('#controls'),key,label,min,max,value,(k,v)=>post('/api/control',{mode:'manual',controls:k==='opening'?{opening:v,seal:v<.01?1:0}:{[k]:v}}));
for(const [key,label,min,max,value] of [['max_jaw_angle','Opening arc',.1,.65,.36],['recession','Backward recession',0,.35,.12],
 ['opening_gamma','Conversational restraint',.6,2,1],['pose_contrast','Shape contrast',1,4,2.5],
 ['opening_contrast','Small / large contrast',1,4,3.2],['key_pose_strength','Key pose strength',0,1,.95],
 ['accent_gain','Opening accents',0,.5,.45],['front_motion_scale','Front lip motion',0,1,.8],
 ['rounding_reach','Rounded forward reach',0,1,1],['lower_lip_spike','Lower lip spike',0,1,0],
 ['v_depth','Rear V point',.02,.30,.11]])
 if((!character||key!=='v_depth')&&!(character?.schema===2&&key==='recession'))slider($('#styles'),key,character?.schema===2&&key==='max_jaw_angle'?'Opening strength':label,min,max,value,(k,v)=>post('/api/style',{[k]:v}));
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>post('/api/control',{mode:b.dataset.mode}));
const presets={rest:{...REST},open:{...REST,opening:.65,seal:0},round:{...REST,opening:.5,rounding:.9,seal:0},
 smile:{...REST,opening:.55,corner_left:.8,corner_right:.8,seal:0},smirk:{...REST,opening:.22,corner_left:.9,corner_right:.05,seal:0}};
for(const b of document.querySelectorAll('[data-preset]'))b.onclick=()=>{
 const {opening,rounding,spread,seal,corner_left,corner_right}=presets[b.dataset.preset];
 post('/api/control',{mode:'manual',controls:{opening,rounding,spread,seal,corner_left,corner_right}});
};
$('#mask').onchange=e=>renderers.forEach(r=>r.options.mask=e.target.checked);
$('#placement').onchange=e=>$('.panels').classList.toggle('placement',e.target.checked);
$('#density').onchange=e=>renderers.forEach(r=>r.options.grid=Number(e.target.value));
for(const [key,label] of [['neutral','1 · Rest / lips together'],['open','2 · Open comfortably'],['wide','3 · Ee / spread'],['narrow','4 · Oo / narrow'],['smile','5 · Closed smile']]){
 const b=document.createElement('button');b.textContent=label;b.onclick=()=>post('/api/calibration/start',{stage:key});$('#calibration-stages').append(b);
}
$('#stop-capture').onclick=()=>post('/api/calibration/stop');$('#save-calibration').onclick=()=>post('/api/calibration/save');

const events=new EventSource('/api/events');
events.onmessage=e=>{
 const next=JSON.parse(e.data);if(!next.pose||next.sequence<=lastSequence)return;lastSequence=next.sequence;state=next;
 $('#connection').textContent=next.mode==='live'?(next.tracking?'● Live tracking':'○ Waiting for tracker'):'● Preview connected';
 const expression=next.expression?.parts;
 $('#scene').textContent=expression?`${expression.mouth.selected} / ${expression.eyes.selected} · ${next.label}`:next.label;$('#status').textContent=next.mode==='live'?(next.age_ms===null?'No frame':`${next.age_ms} ms since input`):'Shared pose · independent corners';
 $('#calibrated').textContent=next.calibrated?'Wearer profile loaded':'Default ranges';
 const cal=next.calibration;$('#calibration-status').textContent=`${cal.stage?'Capturing '+cal.stage+' · ':''}${Object.entries(cal.counts).map(([k,v])=>`${k}: ${v}`).join(' / ')}`;
 document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('selected',b.dataset.mode===next.mode));
 if(next.mode!=='manual'||!document.activeElement?.matches('input[type=range]')){
  for(const input of $('#controls').querySelectorAll('input')){
   input.value=next.pose[input.dataset.key];input.previousElementSibling.textContent=Number(input.value).toFixed(2);
  }
 }
};
events.onerror=()=>$('#connection').textContent='○ Reconnecting';
function animate(){
 // Present each authored character frame as-is. Browser refresh does not add
 // intermediate poses or smooth away a one-frame transition at 24 fps.
 if(state.sequence!==lastRendered){
  lastRendered=state.sequence;current={...state.pose};
  for(const renderer of renderers)renderer.draw(current,state.style);
 }
 requestAnimationFrame(animate);
}
window.prootface={renderers,get state(){return state;},get pose(){return current;}};
if(character?.schema===2)$('#mask').checked=false;
requestAnimationFrame(animate);
