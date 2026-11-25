"""Render the implemented flat-screen character to an audible speaking clip.

python tools/synthesize_example.py local/sentence
python tools/render_sentence.py --character local/character.json --output local/preview

Uses the same JS deformation and Python Animator as the live preview, with
Pillow rasterization (not a browser/hardware capture). Requires numpy/Pillow,
Node and ffmpeg. Character-derived images stay private under local/.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from prootface.model import Animator
from prootface.performance import SpeakingExample


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--character', type=Path, default=Path('local/character.json'))
    parser.add_argument('--speech', type=Path, default=Path('local/sentence'))
    parser.add_argument('--output', type=Path, default=Path('local/preview'))
    parser.add_argument('--fps', type=int, default=60)
    parser.add_argument('--speed', type=float, default=.85)
    args = parser.parse_args()
    if not 12 <= args.fps <= 120 or not .5 <= args.speed <= 2:
        parser.error('Use 12–120 fps and .5–2 speech speed')
    args.output.mkdir(parents=True, exist_ok=True)
    character = json.loads(args.character.read_text())
    if character.get('schema') != 1:
        parser.error('Legacy silhouette renderer only; use tools/render_morph_sentence.py for an authored mesh')
    example = SpeakingExample(json.loads((args.speech/'phonemes.json').read_text()))
    before, after = .65, .85
    duration = before+example.duration/args.speed+after
    frames = math.ceil(duration*args.fps)
    animator = Animator()
    poses = [animator.step(example.controls((i/args.fps-before)*args.speed), i/args.fps)
             for i in range(frames)]
    # One JS call evaluates both anatomical sides for every actual output frame.
    script = """
import fs from 'node:fs';
import {buildCharacter} from './prootface/web/character.mjs';
import {WS_STUDY_MASK} from './prootface/web/mouth.mjs';
const {character,poses}=JSON.parse(fs.readFileSync(0,'utf8'));
const frames=poses.map(pose=>Object.fromEntries(['left','right'].map(side=>[side,
 buildCharacter(character,pose,{},side).parts.map(p=>({name:p.name,outline:p.outline}))])));
process.stdout.write(JSON.stringify({frames,mask:WS_STUDY_MASK}));
"""
    result = subprocess.run(['node','--input-type=module','-e',script], cwd=ROOT,
                            input=json.dumps(dict(character=character,poses=poses)),
                            text=True,capture_output=True,check=True)
    geometry = json.loads(result.stdout)
    font_file = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    font = lambda size:ImageFont.truetype(font_file,size)
    small, label_font, sentence_font = font(17), font(14), font(32)
    width, height = 1280, 720
    movie = args.output/'speaking-example.mp4'
    command = ['ffmpeg','-y','-hide_banner','-loglevel','error',
               '-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{height}',
               '-r',str(args.fps),'-i','pipe:0','-i',str(args.speech/'voice.wav'),
               '-filter_complex',f'[1:a]atempo={args.speed},adelay={round(before*1000)},apad[a]',
               '-map','0:v','-map','[a]','-t',str(frames/args.fps),
               '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',
               '-c:a','aac','-b:a','128k','-movflags','+faststart',str(movie)]
    samples = []
    sample_indices = {0,round((before+.37/args.speed)*args.fps),
                      round((before+.43/args.speed)*args.fps),
                      round((before+1.08/args.speed)*args.fps),
                      round((before+1.95/args.speed)*args.fps),frames-1}
    color = tuple(round(x*255) for x in character.get('color',[.2,.8,1,1])[:3])
    with (args.output/'encode.log').open('w') as log:
        process = subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log)
        try:
            for index, pose in enumerate(poses):
                seconds = index/args.fps
                voice_time = (seconds-before)*args.speed
                board = Image.new('RGB',(width,height),'#0a0e14')
                draw = ImageDraw.Draw(board)
                draw.text((40,29),'prootface / speaking study',font=font(24),fill='#e4ebf2')
                draw.text((40,66),'Supplied rest shape · independent motion · two flat side displays',font=small,fill='#8d9daf')
                words = example.text.split()
                word_widths = [draw.textlength(word,font=sentence_font) for word in words]
                x = (width-sum(word_widths)-14*(len(words)-1))/2
                active = example.word(voice_time)
                for word, word_width in zip(words,word_widths):
                    selected = word.lower().strip('.,!?') == active
                    draw.text((x,113),word,font=sentence_font,fill='#6eacff' if selected else '#e5ebf3')
                    x += word_width+14
                for column, side in enumerate(('left','right')):
                    x, y, w, h = 40+612*column, 215, 588, 331
                    face = Image.new('RGB',(w*2,h*2),'black')
                    fd = ImageDraw.Draw(face)
                    for part in geometry['frames'][index][side]:
                        polygon=[]
                        for px,py in part['outline']:
                            u=px/3.76+.5
                            if side=='left':u=1-u
                            v=.5-(py+.14)/2.32
                            polygon.append((u*w*2,v*h*2))
                        fd.polygon(polygon,fill=color)
                    face = face.resize((w,h),Image.Resampling.LANCZOS)
                    board.paste(face,(x,y))
                    draw.rectangle((x,y,x+w,y+h),outline='#22303e',width=1)
                    draw.text((x,y-27),side.upper()+' SIDE',font=label_font,fill='#8d9daf')
                if pose['seal']>.98:
                    motion='Lip contact · expression holds'
                elif pose['rounding']>.50:
                    motion='Rounded articulation · corner shape retained'
                else:
                    motion='Opening and recession · expression holds'
                draw.text((40,576),motion,font=small,fill='#b7c7d8')
                draw.rounded_rectangle((40,620,1240,624),radius=2,fill='#1e2b39')
                draw.rounded_rectangle((40,620,40+1200*index/max(1,frames-1),624),radius=2,fill='#417fdd')
                draw.text((40,657),'Procedural review render · synthesized speech · no avatar phoneme shapes',font=small,fill='#8092a7')
                process.stdin.write(board.tobytes())
                if index in sample_indices:
                    sample=board.resize((640,360),Image.Resampling.LANCZOS)
                    samples.append(sample)
                if index==round((before+.37/args.speed)*args.fps):
                    board.save(args.output/'poster.png')
        finally:
            process.stdin.close()
        if process.wait()!=0:
            raise RuntimeError((args.output/'encode.log').read_text())
    contact_sheet=Image.new('RGB',(1280,1080))
    for index, sample in enumerate(samples[:6]):
        contact_sheet.paste(sample,((index%2)*640,(index//2)*360))
    contact_sheet.save(args.output/'review-frames.png')
    metadata=dict(text=example.text,fps=args.fps,duration=frames/args.fps,
                  frames=frames,audio_speed=args.speed,avatar_phoneme_keys_used=False,
                  source='Private rest silhouette; Python Animator + JS procedural character deformation',
                  checks=dict(full_contact_frames=sum(p['seal']>=.999 for p in poses),
                              max_opening=max(p['aperture'] for p in poses),
                              max_rounding=max(p['rounding'] for p in poses)))
    (args.output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(metadata))
    print(movie)


if __name__=='__main__':
    main()
