"""Review source footage beside a real-measurement-driven native character render.

Offline review only. Does not alter measurements, infer phones or offset the
audio to hide controller delay. Requires ffmpeg, Blender and a private rig.
"""
import argparse
import base64
import json
from pathlib import Path
import struct
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from prootface.openseeface import HEADER
from prootface.timing import ANIMATION_FPS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--packets', type=Path, required=True)
    parser.add_argument('--replay', type=Path, required=True)
    parser.add_argument('--character', type=Path, default=Path('local/character.json'))
    args = parser.parse_args()
    output = args.replay
    metadata = json.loads((output/'replay.json').read_text())
    measurements = json.loads((output/'measurements.json').read_text())
    start, end = metadata['evaluation']
    source_frames = output/'source-frames'
    source_frames.mkdir(exist_ok=True)
    subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-ss',str(start),
                    '-i',str(args.source),'-t',str(end-start),'-vf','fps=24',
                    '-start_number','0',str(source_frames/'%05d.png')],check=True)
    frames = output/'frames'
    with (output/'blender.log').open('w') as log:
        subprocess.run(['blender','--background','--factory-startup','--disable-autoexec',
                        '--python',str(ROOT/'tools/render_morph_frames.py'),'--',
                        '--character',str(args.character.resolve()),'--poses',str((output/'poses.json').resolve()),
                        '--output',str(frames.resolve())],stdout=log,stderr=subprocess.STDOUT,check=True)

    # Fixed review crops, derived only for presentation. They never drive poses.
    mouth_points = []
    for line in args.packets.read_text().splitlines():
        row = json.loads(line)
        if start <= row['time'] < end and row['packet']:
            data = base64.b64decode(row['packet'])
            xy = np.array(struct.unpack_from('<136f',data,HEADER.size+68*4)).reshape(-1,2)
            mouth_points.extend(xy[48:66])
    points = np.array(mouth_points)
    xmin,ymin = points.min(axis=0);xmax,ymax = points.max(axis=0)
    human_crop = (int(xmin-12),int(ymin-12),int(xmax+12),int(ymax+12))
    masks = []
    for path in sorted(frames.glob('*.png')):
        pixels = np.array(Image.open(path).convert('RGB'))
        # Review camera is fixed. Mouth is below the eye; retain the attached V.
        ys,xs = np.where((pixels[:,:,2]>140)&(pixels[:,:,0]<60)&
                         (np.indices(pixels.shape[:2])[0]>250))
        if len(xs):masks.append((xs.min(),ys.min(),xs.max()+1,ys.max()+1))
    if not masks:raise ValueError('No visible mouth in review render')
    avatar_crop = (min(b[0] for b in masks)-12,min(b[1] for b in masks)-12,
                   max(b[2] for b in masks)+12,max(b[3] for b in masks)+12)
    font = lambda size: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)
    movie = output/'real-video-24fps.mp4'
    command = ['ffmpeg','-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24',
               '-s','1280x760','-r',str(ANIMATION_FPS),'-i','pipe:0','-ss',str(start),'-i',str(args.source),
               '-t',str(end-start),'-map','0:v','-map','1:a:0','-c:v','libx264','-crf','18',
               '-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(movie)]
    boards = []
    with (output/'encode.log').open('w') as log:
        process = subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log)
        for i,row in enumerate(measurements):
            human = Image.open(source_frames/f'{i:05}.png').convert('RGB')
            avatar = Image.open(frames/f'{i:05}.png').convert('RGB')
            board = Image.new('RGB',(1280,760),'#0a0e14');draw = ImageDraw.Draw(board)
            draw.text((25,20),'Real footage → OpenSeeFace → prootface',font=font(28),fill='#edf3fa')
            draw.text((25,62),'24 fps · measured movement · causal live controller · original audio',font=font(18),fill='#9cb1c8')
            draw.text((25,107),'Source video',font=font(21),fill='#e4ebf4')
            draw.text((545,107),'Character response',font=font(21),fill='#e4ebf4')
            board.paste(ImageOps.pad(human,(490,350),color='black'),(25,145))
            board.paste(ImageOps.pad(avatar,(710,350),color='black'),(545,145))
            draw.text((25,512),'Measured lips',font=font(19),fill='#9cb1c8')
            draw.text((545,512),'Mouth detail',font=font(19),fill='#9cb1c8')
            board.paste(ImageOps.pad(human.crop(human_crop),(490,135),color='black'),(25,543))
            board.paste(ImageOps.pad(avatar.crop(avatar_crop),(710,135),color='black'),(545,543))
            status='tracked' if row['tracking'] else 'tracking lost / relaxing'
            draw.text((25,698),f'{start+i/24:.2f}s · {status} · earlier-section estimated calibration',font=font(16),fill='#9cb1c8')
            draw.text((25,729),'Source: The White House, 23 Jan 2016 · public domain · cropped for comparison',font=font(14),fill='#7289a2')
            process.stdin.write(board.tobytes())
            boards.append(board)
        process.stdin.close()
        if process.wait():raise RuntimeError((output/'encode.log').read_text())
    boards[len(boards)//2].save(output/'poster.png')
    # GIF timestamps alternate 4/5 centiseconds to preserve the 24 fps clock.
    durations=[round((i+1)*1000/24/10)*10-round(i*1000/24/10)*10 for i in range(len(boards))]
    small=[im.resize((1024,608),Image.Resampling.LANCZOS).quantize(colors=128) for im in boards]
    small[0].save(output/'real-video-24fps.gif',save_all=True,append_images=small[1:],
                  duration=durations,loop=0,optimize=False,disposal=2)
    print(movie)


if __name__=='__main__':main()
