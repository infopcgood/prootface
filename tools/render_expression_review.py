"""Render the same captured speech poses across expression banks, then triggers.

All supplied character data and recordings remain private. This is an offline
replay of controller poses, not a live camera or device latency measurement.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prootface.expressions import ExpressionController, ExpressionRig
from prootface.offscreen import OffscreenRenderer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--character', type=Path, required=True)
    parser.add_argument('--poses', type=Path, required=True, help='Flat 24 Hz Animator pose list')
    parser.add_argument('--audio', type=Path, help='Optional aligned audio or video clip, looped')
    parser.add_argument('--comparison-part', choices=('mouth','face'), default='mouth',
                        help='Keep eyes neutral during the comparison by default')
    parser.add_argument('--output', type=Path, default=Path('local/expression-review'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    character = json.loads(args.character.read_text())
    poses = json.loads(args.poses.read_text())
    if not isinstance(poses, list) or not poses:
        raise ValueError('Expected a nonempty controller pose list')
    rig = ExpressionRig(character)
    names = rig.available
    width, height = max(1000, len(names)*300), 500
    fps, count = 24, len(poses)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 21)
        small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16)
    except OSError:
        font = small = ImageFont.load_default()
    controllers = {}
    for name in names:
        controller = ExpressionController(names)
        controller.select(name, 0., part=args.comparison_part, transition=0.)
        controllers[name] = controller
    buttons = ExpressionController(names)
    selected = None
    movie = args.output/'expression-speech-24fps.mp4'
    command = ['ffmpeg','-y','-hide_banner','-loglevel','error','-f','rawvideo',
               '-pix_fmt','rgb24','-s',f'{width}x{height}','-r',str(fps),'-i','pipe:0']
    if args.audio:
        command += ['-stream_loop','-1','-i',str(args.audio),'-map','0:v','-map','1:a:0',
                    '-c:a','aac','-b:a','128k']
    command += ['-t',str(2*count/fps),'-c:v','libx264','-crf','18','-preset','fast',
                '-pix_fmt','yuv420p','-movflags','+faststart',str(movie)]
    samples = []
    with (args.output/'encode.log').open('w') as log, OffscreenRenderer(args.character,384,216) as renderer:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log)
        try:
            for i in range(2*count):
                board = Image.new('RGB',(width,height),'#0b1018')
                draw = ImageDraw.Draw(board)
                draw.text((20,12),'Expression-specific speech / 24 fps',font=font,fill='#e3edf8')
                base = poses[i % count]
                if i < count:
                    label = ('Neutral eyes; ' if args.comparison_part == 'mouth' else '')
                    draw.text((20,44),label+'same recorded speech in every column; both anatomical views.',font=small,fill='#a8bbd0')
                    cell_width = width//len(names)
                    for j,name in enumerate(names):
                        weights = controllers[name].sample(i/fps)
                        frame = renderer.render_atlas(rig.compose(base,weights))
                        draw.text((j*cell_width+18,76),name.upper(),font=font,fill='#8abaff')
                        for row,view in enumerate((frame[:,:384],frame[:,384:])):
                            image = Image.fromarray(np.ascontiguousarray(view[:,:,::-1]))
                            image = image.resize((cell_width,169),Image.Resampling.LANCZOS)
                            board.paste(image,(j*cell_width,109+row*180))
                else:
                    t = (i-count)/fps
                    name = names[min(len(names)-1,int((i-count)*len(names)/count))]
                    if name != selected:
                        buttons.select(name,t)
                        selected = name
                    frame = renderer.render_atlas(rig.compose(base,buttons.sample(t)))
                    draw.text((20,44),'External button: '+name.upper()+' / 200 ms transition / speech continues',
                              font=small,fill='#8abaff')
                    view_width = (width-60)//2
                    for j,view in enumerate((frame[:,:384],frame[:,384:])):
                        image = Image.fromarray(np.ascontiguousarray(view[:,:,::-1]))
                        image = image.resize((view_width,int(view_width*216/384)),Image.Resampling.LANCZOS)
                        board.paste(image,(20+j*(view_width+20),80))
                draw.text((20,478),'Offline replay; button selections simulated. No on-device latency claim.',font=small,fill='#a8bbd0')
                if i in (count//3, count+count//2):
                    samples.append(board.copy())
                process.stdin.write(board.tobytes())
        finally:
            process.stdin.close()
        if process.wait():
            raise RuntimeError((args.output/'encode.log').read_text())
    if samples:
        poster = Image.new('RGB',(width,height*len(samples)))
        for i,sample in enumerate(samples):
            poster.paste(sample,(0,i*height))
        poster.save(args.output/'review.png')
    (args.output/'review.json').write_text(json.dumps(dict(
        fps=fps, frames=2*count, expressions=names, comparison_part=args.comparison_part,
        recorded_pose_replay=True,
        external_selections_simulated=True, controller_future_inputs=False),indent=2)+'\n')
    print(movie, flush=True)


if __name__ == '__main__':
    main()
