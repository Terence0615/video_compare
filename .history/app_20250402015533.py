from flask import Flask, render_template, jsonify, send_from_directory
import os
import pandas as pd
from math import ceil

app = Flask(__name__)

# 每页显示的视频数量
VIDEOS_PER_PAGE = 12

def get_video_data():
    # 读取Excel文件获取prompt
    df = pd.read_excel('视频提示词结果_20250401_231849.xlsx')
    
    # 获取视频文件列表
    tongyi_videos = sorted([f for f in os.listdir('results/tongyi') if f.endswith('.mp4')])
    wavespeed_videos = sorted([f for f in os.listdir('results/wavespeed') if f.endswith('.mp4')])
    
    # 构建视频数据
    videos = []
    for i, (tongyi_video, wavespeed_video) in enumerate(zip(tongyi_videos, wavespeed_videos)):
        video_index = i + 1
        videos.append({
            'id': video_index,
            'prompt': df.iloc[i]['video_prompt'],
            'tongyi_url': f'/results/tongyi/{tongyi_video}',
            'wavespeed_url': f'/results/wavespeed/{wavespeed_video}'
        })
    
    return videos

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/videos/<int:page>')
def get_videos(page):
    videos = get_video_data()
    start_idx = (page - 1) * VIDEOS_PER_PAGE
    end_idx = start_idx + VIDEOS_PER_PAGE
    page_videos = videos[start_idx:end_idx]
    
    return jsonify({
        'videos': page_videos,
        'total_pages': ceil(len(videos) / VIDEOS_PER_PAGE)
    })

@app.route('/results/<path:filename>')
def serve_video(filename):
    return send_from_directory('results', filename)

if __name__ == '__main__':
    app.run(debug=True) 