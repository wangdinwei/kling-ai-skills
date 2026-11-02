#!/usr/bin/env python3
"""帧精确拼接：分段 -frames:v 编码 → concat demuxer → 合原曲（音频 stream copy）

为什么不用单次 filter_complex + concat：实测会静默丢帧（4514 帧只剩 4447）。
为什么不用逐段 -t：每段 ±1 帧取整误差会累积（23 段偏 +0.1s）。

用法：改下面的 SEGS / SONG / 路径，然后
  python3 assemble_frame_exact.py --list     # 先核帧级时间轴
  python3 assemble_frame_exact.py            # 出片
  python3 assemble_frame_exact.py --rough    # 缺素材处放占位块
"""
import os, subprocess, sys

# ── 配置 ────────────────────────────────────────────────
ROOT    = '/path/to/project'          # 素材根目录
BUILD   = os.path.join(ROOT, 'build')
SEGDIR  = os.path.join(BUILD, 'segs')
SONG    = '/path/to/song.mp3'
SONG_DUR = 150.456                    # 原曲时长，用 ffprobe 实测后填
W, H, FPS = 1268, 724, 30
DIRS = {'lip': 'lipsync', 'raw': 'kling_videos', 'fill': 'fillers', 'png': '首帧'}

# (段名, 素材前缀:文件名, 起始秒, 结束秒, 追加定格秒, 说明)
# 结束秒一律落在 SRT 句末或句间空档；lip: 段只能放在它自己的音频起点
SEGS = [
    # ('01a', 'lip:01', 0.020, 9.987, 0.0, '第一句歌词'),
]
# ────────────────────────────────────────────────────

def f(t):
    return int(round(t * FPS))

VF = (f'scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},'
      f'fps={FPS},setsar=1,format=yuv420p')
ENC = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-r', str(FPS)]

def resolve(src):
    if src in ('BLACK',) or src.startswith('GAP:'):
        return None, src
    kind, fn = src.split(':', 1)
    ext = {'png': '.png', 'lip': '.mp4', 'raw': '.mp4', 'fill': '.mp4'}[kind]
    return os.path.join(ROOT, DIRS[kind], fn + ext), kind

def count_frames(p):
    return int(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                               '-count_frames', '-show_entries', 'stream=nb_read_frames',
                               '-of', 'default=nw=1:nk=1', p],
                              capture_output=True, text=True).stdout.strip() or 0)

def main():
    rough = '--rough' in sys.argv
    if '--list' in sys.argv:
        tot = 0
        for name, src, a, b, pad, note in SEGS:
            n = f(b) - f(a); tot += n
            print(f'{name:7s} {a:7.3f}-{b:7.3f} {n:4d}帧 {n/FPS:6.3f}s  {src:16s} {note}')
        print(f'\n合计 {tot} 帧 = {tot/FPS:.3f}s   原曲 {SONG_DUR}s   差 {tot/FPS-SONG_DUR:+.3f}s')
        return

    os.makedirs(SEGDIR, exist_ok=True)
    seg_files, short = [], []
    for i, (name, src, a, b, pad, note) in enumerate(SEGS):
        n = f(b) - f(a)
        dst = os.path.join(SEGDIR, f'{i:02d}_{name}.mp4')
        path, kind = resolve(src)
        if path is None or not os.path.exists(path):
            if path is not None and not rough:
                raise SystemExit(f'{name} 缺素材 {path}')
            color = '#000000' if src == 'BLACK' else '#141a33'
            cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi',
                   '-i', f'color=c={color}:s={W}x{H}:r={FPS}:d={n/FPS+1:.3f}',
                   '-vf', VF, *ENC, '-frames:v', str(n), '-an', dst]
        elif kind == 'png':
            cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1',
                   '-t', f'{n/FPS+1:.3f}', '-i', path,
                   '-vf', VF, *ENC, '-frames:v', str(n), '-an', dst]
        else:
            vf = VF + (f',tpad=stop_mode=clone:stop_duration={pad:.3f}' if pad > 0 else '')
            cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-ss', '0',
                   '-t', f'{n/FPS+pad+1:.3f}', '-i', path,
                   '-vf', vf, *ENC, '-frames:v', str(n), '-an', dst]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f'{name} 编码失败:\n{r.stderr[-600:]}')
        got = count_frames(dst)
        if got != n:
            short.append((name, n, got))
        seg_files.append(dst)
        print(f'[{i:02d}] {name:7s} 目标 {n:4d} 帧  实际 {got:4d} 帧  {note}', flush=True)

    if short:
        print(f'\n⚠ 帧数不符 {len(short)} 段：{short}')

    lst = os.path.join(SEGDIR, 'concat.txt')
    with open(lst, 'w') as fh:
        for s in seg_files:
            fh.write(f"file '{s}'\n")
    merged = os.path.join(BUILD, 'merged_noaudio.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0',
                    '-i', lst, '-c', 'copy', merged], check=True)

    out = os.path.join(BUILD, 'rough_cut.mp4' if rough else 'master.mp4')
    # 不要 -shortest：它会按较短流收尾，实测截掉音频末尾 4.5ms
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', merged, '-i', SONG,
                    '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'copy',
                    '-movflags', '+faststart', out], check=True)

    exp = sum(f(b) - f(a) for _, _, a, b, _, _ in SEGS)
    vf_n = count_frames(out)
    print(f'\n输出 {out}')
    print(f'  帧数 {vf_n} （计划 {exp}，差 {vf_n-exp:+d}）')
    print('  下一步：用 PCM 逐采样比对确认音频未改动')

if __name__ == '__main__':
    main()
