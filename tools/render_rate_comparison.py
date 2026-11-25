"""Compare presentation cadences while preserving controller timing and audio.

The input is an existing constant-rate render. Lower rates hold the latest
available source pose; they never interpolate or select a future pose. This
does not rerun the controller at a slower rate or retime its contact rules.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageOps


def held_source_index(frame, source_fps, output_fps):
    if output_fps <= 0 or source_fps % output_fps:
        raise ValueError('Output rate must be a positive divisor of the source rate')
    stride = source_fps // output_fps
    return frame // stride * stride


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frames', type=Path, required=True)
    parser.add_argument('--movie', type=Path, required=True,
                        help='Matching source-rate movie with synchronized audio')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-fps', type=int, default=24)
    parser.add_argument('--rates', type=int, nargs='+', default=[24,12,6])
    parser.add_argument('--crop', type=int, nargs=4)
    args = parser.parse_args()
    if args.source_fps <= 0 or not args.rates or len(set(args.rates)) != len(args.rates):
        parser.error('Provide a positive source rate and distinct output rates')
    for rate in args.rates:
        held_source_index(0,args.source_fps,rate)
    frames = sorted(args.frames.glob('*.png'))
    if not frames or len(frames) % args.source_fps:
        parser.error('Provide complete seconds of numbered source frames')
    if [p.stem for p in frames] != [f'{i:05}' for i in range(len(frames))]:
        parser.error('Source frames must be contiguous, starting with 00000.png')
    args.output.mkdir(parents=True,exist_ok=True)
    duration = len(frames)/args.source_fps
    summary = dict(source_fps=args.source_fps,duration=duration,rates={},
                   method='Latest-pose sample and hold; unchanged controller, audio and playback speed.')
    for rate in args.rates:
        destination = args.output/f'A-{rate}fps.mp4'
        if rate == args.source_fps:
            shutil.copyfile(args.movie,destination)
        else:
            stride = args.source_fps//rate
            subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-i',str(args.movie),
                            '-map','0:v:0','-map','0:a:0?',
                            '-vf',f'select=not(mod(n\\,{stride})),setpts=N/({rate}*TB)',
                            '-r',str(rate),'-fps_mode','cfr','-t',str(duration),
                            '-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','copy',
                            '-movflags','+faststart',str(destination)],check=True)
        summary['rates'][str(rate)] = dict(frames=len(frames)*rate//args.source_fps,
                                          file=destination.name)
    width,height = 400*len(args.rates),500
    font = lambda size: ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',size)
    movie = args.output/'cadence-comparison.mp4'
    gif = args.output/'cadence-comparison.gif'
    command = ['ffmpeg','-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24',
               '-s',f'{width}x{height}','-r',str(args.source_fps),'-i','pipe:0','-i',str(args.movie),
               '-filter_complex','[0:v]split[vm][vg];[vg]split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle[gif]',
               '-map','[vm]','-map','1:a:0?','-t',str(duration),'-c:v','libx264','-crf','18',
               '-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(movie),
               '-map','[gif]','-an','-loop','0',str(gif)]
    with (args.output/'encode.log').open('w') as log:
        process = subprocess.Popen(command,stdin=subprocess.PIPE,stderr=log)
        cache = {}
        for index in range(len(frames)):
            board = Image.new('RGB',(width,height),'#0a0e14');draw = ImageDraw.Draw(board)
            draw.text((25,20),'A / animation cadence comparison',font=font(26),fill='#e5ebf3')
            draw.text((25,62),'Same performance and audio · normal speed · held poses',font=font(18),fill='#94a9bf')
            for column,rate in enumerate(args.rates):
                selected = held_source_index(index,args.source_fps,rate)
                if selected not in cache:
                    with Image.open(frames[selected]) as image:
                        cache[selected] = ImageOps.contain(image.convert('RGB').crop(args.crop) if args.crop else image.convert('RGB'),(350,285),Image.Resampling.LANCZOS)
                x = column*400+25;image = cache[selected]
                draw.text((x,110),f'{rate} fps',font=font(25),fill='#dce9fa')
                tile = Image.new('RGB',(350,285));tile.paste(image,((350-image.width)//2,(285-image.height)//2))
                board.paste(tile,(x,155));draw.rectangle((x,155,x+350,440),outline='#22303e')
            draw.text((25,466),f'Tracking and controller unchanged at {args.source_fps} fps · A lower lip · stronger forward rounding',font=font(15),fill='#879bb1')
            process.stdin.write(board.tobytes())
            if index==len(frames)//2:board.save(args.output/'poster.png')
            # Future iterations only need current/future source images.
            cache={k:v for k,v in cache.items() if k>=index-args.source_fps//min(args.rates)}
        process.stdin.close()
        if process.wait():
            raise RuntimeError((args.output/'encode.log').read_text())
    (args.output/'comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))


if __name__=='__main__':main()
