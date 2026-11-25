"""Render the actual procedural mesh without a browser (optional numpy/Pillow).

This is a software geometry review, not a WebGL/browser or hardware test.
Run from the repository root: python tools/render_study.py output.png
"""

import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from prootface.model import NEUTRAL, Style, pose_from_controls


def geometry(pose, side):
    code = "import {buildMouth,WS_STUDY_MASK} from './prootface/web/mouth.mjs';"
    code += f"const m=buildMouth({json.dumps(pose)},{{}},{json.dumps(side)});"
    code += "console.log(JSON.stringify({mask:WS_STUDY_MASK,parts:m.parts.map(p=>({name:p.name,positions:Array.from(p.positions),normals:Array.from(p.normals),colors:Array.from(p.colors)}))}));"
    return json.loads(subprocess.check_output(["node", "--input-type=module", "-e", code], cwd=ROOT))


def render(pose, side, width=660, height=370):
    model = geometry(pose, side)
    pixels = np.zeros((height, width, 3), dtype=np.float64)
    depth = np.full((height, width), -np.inf)
    light = np.array([-.4, .8, 1.3]); light /= np.linalg.norm(light)
    for part in model["parts"]:
        positions = np.array(part["positions"]).reshape(-1, 3)
        normals = np.array(part["normals"]).reshape(-1, 3)
        colors = np.array(part["colors"]).reshape(-1, 4)
        projected = positions.copy()
        projected[:, 0] = (positions[:, 0]/1.88*(1 if side == "right" else -1)*.5+.5)*(width-1)
        projected[:, 1] = (.5-(positions[:, 1]+.14)/1.16*.5)*(height-1)
        for i in range(0, len(projected), 3):
            p=projected[i:i+3];c=colors[i:i+3];n=normals[i]
            xmin,xmax=max(0,int(np.floor(p[:,0].min()))),min(width-1,int(np.ceil(p[:,0].max())))
            ymin,ymax=max(0,int(np.floor(p[:,1].min()))),min(height-1,int(np.ceil(p[:,1].max())))
            if xmin>xmax or ymin>ymax: continue
            a,b,d=p
            den=(b[1]-d[1])*(a[0]-d[0])+(d[0]-b[0])*(a[1]-d[1])
            if abs(den)<1e-8: continue
            yy,xx=np.mgrid[ymin:ymax+1,xmin:xmax+1]
            wa=((b[1]-d[1])*(xx-d[0])+(d[0]-b[0])*(yy-d[1]))/den
            wb=((d[1]-a[1])*(xx-d[0])+(a[0]-d[0])*(yy-d[1]))/den
            wc=1-wa-wb
            z=wa*a[2]+wb*b[2]+wc*d[2]
            rgba=wa[...,None]*c[0]+wb[...,None]*c[1]+wc[...,None]*c[2]
            keep=(wa>=-1e-6)&(wb>=-1e-6)&(wc>=-1e-6)&(z>=depth[ymin:ymax+1,xmin:xmax+1])&(rgba[...,3]>.005)
            norm=np.linalg.norm(n)
            n=n/(norm if norm else 1)
            if n[2]<0:n=-n
            diffuse=.32+.68*max(0,float(n@light))
            reflection=-light+2*float(n@light)*n
            shine=0.0
            rgb=rgba[...,:3]*diffuse+shine*np.minimum(1,np.linalg.norm(rgba[...,:3],axis=-1)[...,None]*2)
            alpha=rgba[...,3,None]
            region=pixels[ymin:ymax+1,xmin:xmax+1]
            blended=rgb*alpha+region*(1-alpha)
            region[keep]=blended[keep]
            depth[ymin:ymax+1,xmin:xmax+1][keep]=z[keep]
    result=Image.fromarray((np.clip(pixels,0,1)*255).astype(np.uint8))
    mask=Image.new('L',(width,height));draw=ImageDraw.Draw(mask)
    polygon=[((1-u if side=='left' else u)*(width-1),v*(height-1)) for u,v in model['mask']]
    draw.polygon(polygon,fill=255)
    result=Image.composite(result,Image.new('RGB',result.size),mask)
    return result


def main():
    destination=Path(sys.argv[1] if len(sys.argv)>1 else 'local/mouth-study.png')
    destination.parent.mkdir(parents=True,exist_ok=True)
    board=Image.new('RGB',(1440,1000),'#0d100f');draw=ImageDraw.Draw(board)
    font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    font=ImageFont.truetype(font_path,17) if Path(font_path).exists() else ImageFont.load_default()
    title=ImageFont.truetype(font_path,28) if Path(font_path).exists() else font
    draw.text((40,28),'prootface / revised contour study',font=title,fill='#d9d6cf')
    draw.text((40,72),'Provisional shape · no tongue or tooth rows · one attached rear V per side',font=font,fill='#8c9890')
    for row,(label,controls) in enumerate([
        ('01 / Lip contact with a restrained smile',dict(opening=.4,seal=1,corner_left=.4,corner_right=.4)),
        ('02 / Conversational opening, lower jaw receding',dict(opening=.65,seal=0,corner_left=.35,corner_right=.35)),
    ]):
        y=125+row*425
        draw.text((40,y),label,font=font,fill='#c5a67f')
        pose=pose_from_controls({**NEUTRAL,**controls},Style())
        for col,side in enumerate(('left','right')):
            image=render(pose,side)
            board.paste(image,(40+700*col,y+32))
    draw.text((40,963),'Software geometry review. Shape is pending approval; browser and physical visor appearance are unverified.',font=font,fill='#78867c')
    board.save(destination)
    print(destination)


if __name__=='__main__':main()
