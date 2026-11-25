"""Audible close-up review of the authored pose blendspace, with fixed framing.

python tools/render_morph_sentence.py --character local/character.json

Native rendering and the WebGL mesh use the same configured pose basis and
the same Python-generated blend weights. This is not a browser capture.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from prootface.model import Animator,Style,pose_from_controls
from prootface.performance import SpeakingExample
from prootface.timing import ANIMATION_FPS


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--character',type=Path,default=Path('local/character.json'))
    parser.add_argument('--speech',type=Path,default=Path('local/sentence'))
    parser.add_argument('--output',type=Path,default=Path('local/morph-preview'))
    parser.add_argument('--fps',type=int,choices=[ANIMATION_FPS],default=ANIMATION_FPS)
    parser.add_argument('--speed',type=float,default=.85)
    parser.add_argument('--input-mode',choices=['tracking','authored'],default='tracking',
                        help='Tracking: synthetic camera-supported controls through causal live controller; authored: full pose reference')
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    example=SpeakingExample(json.loads((args.speech/'phonemes.json').read_text()))
    before,after=.65,.85
    controls,exposures=example.keyed_frames(before,after,args.speed)
    count=len(controls)
    if args.input_mode=='tracking':
        animator=Animator()
        for control in controls:
            for key in ('bite','sibilant','postalveolar','rhotic','lip_press'):control[key]=0
        poses=[animator.step(control,i/ANIMATION_FPS) for i,control in enumerate(controls)]
    else:
        poses=[pose_from_controls(control,Style()) for control in controls]
    poses_path=args.output/'poses.json';poses_path.write_text(json.dumps(poses))
    with (args.output/'blender.log').open('w') as log:
        subprocess.run(['blender','--background','--factory-startup','--disable-autoexec','--python',
                        str(ROOT/'tools/render_morph_frames.py'),'--','--character',str(args.character.resolve()),
                        '--poses',str(poses_path.resolve()),'--output',str((args.output/'frames').resolve())],
                       stdout=log,stderr=subprocess.STDOUT,check=True)
    font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    font=lambda size:ImageFont.truetype(font_path,size)
    movie=args.output/f'speaking-{ANIMATION_FPS}fps.mp4'
    command=['ffmpeg','-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24',
             '-s','1200x820','-r',str(args.fps),'-i','pipe:0','-i',str(args.speech/'voice.wav'),
             '-filter_complex',f'[1:a]atempo={args.speed},adelay={round(before*1000)},apad[a]',
             '-map','0:v','-map','[a]','-t',str(count/args.fps),'-c:v','libx264','-crf','18',
             '-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k',
             '-movflags','+faststart',str(movie)]
    selected={0,round((before+.37/args.speed)*args.fps),round((before+.43/args.speed)*args.fps),
              round((before+.9/args.speed)*args.fps),round((before+1.08/args.speed)*args.fps),
              round((before+1.95/args.speed)*args.fps)}
    samples=[]
    with (args.output/'encode.log').open('w') as log:
        process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log)
        try:
            for index,pose in enumerate(poses):
                board=Image.new('RGB',(1200,820),'#0a0e14');draw=ImageDraw.Draw(board)
                draw.text((40,25),'prootface / expressive pass · 24 fps',font=font(25),fill='#e5ebf3')
                subtitle=('Synthetic tracking controls · causal live controller · 24 fps' if args.input_mode=='tracking' else
                          'Scripted pose reference · full consonant hints · 24 fps')
                draw.text((40,64),subtitle,font=font(17),fill='#94a9bf')
                text=example.text;active=example.word((index/args.fps-before)*args.speed)
                words=text.split();f=font(31);widths=[draw.textlength(w,font=f) for w in words]
                x=(1200-sum(widths)-12*(len(words)-1))/2
                for word,w in zip(words,widths):
                    draw.text((x,113),word,font=f,fill='#70afff' if word.lower().strip('.,!?')==active else '#e5ebf3');x+=w+12
                face=Image.open(args.output/'frames'/f'{index:05}.png').convert('RGB')
                board.paste(face.resize((1120,630),Image.Resampling.LANCZOS),(40,163))
                draw.rectangle((40,163,1160,793),outline='#22303e')
                if index in selected:samples.append(board.resize((600,410),Image.Resampling.LANCZOS))
                if index==round((before+.37/args.speed)*args.fps):board.save(args.output/'poster.png')
                process.stdin.write(board.tobytes())
        finally:process.stdin.close()
        if process.wait():raise RuntimeError((args.output/'encode.log').read_text())
    review=Image.new('RGB',(1200,1230))
    for i,sample in enumerate(samples):review.paste(sample,((i%2)*600,(i//2)*410))
    review.save(args.output/'review-frames.png')
    metadata=dict(text=example.text,frames=count,fps=args.fps,duration=count/args.fps,
                  basis='Privately configured authored poses',camera='Fixed, bounded across the pose basis',
                  browser_capture=False,exposures=exposures,input_mode=args.input_mode,
                  live_recording=False,future_frames_used_by_controller=0)
    (args.output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(movie,flush=True)


if __name__=='__main__':main()
