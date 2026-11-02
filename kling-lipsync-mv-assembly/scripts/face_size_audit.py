#!/usr/bin/env python3
"""逐镜量「脸高占画面高」，决定哪些镜头值得跑对口型。

用法：
  python3 face_size_audit.py <视频目录> [帧数采样=6]
  python3 face_size_audit.py <目录> 6 --json

判读（脸高/画面高）：
  ≥25%   近景，口型可辨 → 值得跑 lip-sync
  14–22% 中等，看得到嘴动但看不清字形 → 不值得跑
  <15%   太小 → 绝对不跑，直接用原片
  无正面人脸 → 口型完全看不见

纪律：开工前先跑这个，再决定对口型预算。跳过这一步就是拿钱赌构图。
"""
import glob
import json
import os
import sys

import cv2
import numpy as np

CASCADE = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'


def measure(path, samples=6):
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        cap.release()
        return 0.0, 0, 0
    idxs = [int(total * i / samples) for i in range(samples)]
    fc = cv2.CascadeClassifier(CASCADE)
    ratios, hits = [], 0
    for i in idxs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, frame = cap.read()
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        h_frame = gray.shape[0]
        boxes = fc.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
        if len(boxes):
            hits += 1
            x, y, w, h = max(boxes, key=lambda b: b[2] * b[3])
            ratios.append(h / h_frame)
    cap.release()
    return (float(np.mean(ratios)) if ratios else 0.0), hits, samples


def verdict(ratio, hits):
    if hits == 0:
        return '无正面人脸 → 口型完全看不见', 'skip'
    if ratio >= 0.25:
        return '近景 → 口型可辨', 'lipsync'
    if ratio >= 0.15:
        return '中等 → 看得到嘴动、看不清字形', 'skip'
    return '脸太小 → 绝对不跑', 'skip'


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    root = sys.argv[1]
    samples = 6
    as_json = '--json' in sys.argv
    for a in sys.argv[2:]:
        if a.isdigit():
            samples = int(a)
    files = sorted(glob.glob(os.path.join(root, '*.mp4')))
    if not files:
        raise SystemExit(f'{root} 下没有 mp4')
    rows, budget = [], {'lipsync': [], 'skip': []}
    for f in files:
        ratio, hits, n = measure(f, samples)
        note, tag = verdict(ratio, hits)
        name = os.path.splitext(os.path.basename(f))[0]
        rows.append({'file': name, 'face_ratio': round(ratio, 4),
                     'detected': hits, 'samples': n, 'verdict': note, 'tag': tag})
        budget[tag].append(name)
        if not as_json:
            print(f'{name:8s}{ratio*100:7.1f}%  检出 {hits}/{n}   {note}')
    if as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        print(f'\n值得跑对口型 {len(budget["lipsync"])} 个：{budget["lipsync"]}')
        print(f'不要跑         {len(budget["skip"])} 个：{budget["skip"]}')
        print('\n结论：只给 lipsync 名单付钱。其余镜头靠表演/空镜/字幕承载。')


if __name__ == '__main__':
    main()
