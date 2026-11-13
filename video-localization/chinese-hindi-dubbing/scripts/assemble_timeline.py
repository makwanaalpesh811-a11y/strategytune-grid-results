#!/usr/bin/env python3
"""Assemble timestamped Hindi WAV segments over a source video.
Manifest entries require: source_start, source_end, audio_file.
Optional: keep_original_audio (default true), original_volume (default 0.08).
"""
import argparse, json, os, subprocess, sys

def run(cmd):
    subprocess.run(cmd, check=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--video', required=True)
    p.add_argument('--manifest', required=True)
    p.add_argument('--output', default='dubbed_hindi.mp4')
    p.add_argument('--original-volume', type=float, default=0.08)
    args=p.parse_args()
    data=json.load(open(args.manifest, encoding='utf-8'))
    entries=data if isinstance(data,list) else data['segments']
    if not entries: raise SystemExit('Manifest has no segments')
    inputs=['-i',args.video]
    for e in entries:
        audio=e.get('audio_file') or e.get('file')
        if not audio or not os.path.isfile(audio): raise SystemExit(f'Missing audio: {audio}')
        inputs += ['-i',audio]
    filters=[f'[0:a]volume={args.original_volume}[orig]']
    labels=[]
    for n,e in enumerate(entries,1):
        start=float(e.get('source_start',e.get('start')))
        end=float(e.get('source_end',e.get('end')))
        if end <= start: raise SystemExit(f'Invalid timing for segment {n}')
        slot=end-start; delay=round(start*1000); label=f's{n}'
        filters.append(f'[{n}:a]apad,atrim=duration={slot:.3f},adelay={delay}:all=1,volume=1.5[{label}]')
        labels.append(f'[{label}]')
    mix='[orig]'+''.join(labels)+f'amix=inputs={len(labels)+1}:duration=first:dropout_transition=0,loudnorm=I=-16:TP=-1.5:LRA=11[aout]'
    filters.append(mix)
    cmd=['ffmpeg','-y',*inputs,'-filter_complex',';'.join(filters),'-map','0:v:0','-map','[aout]','-c:v','copy','-c:a','aac','-b:a','192k','-shortest',args.output]
    run(cmd)
    print(args.output)

if __name__=='__main__': main()
