from flask import Flask, render_template, jsonify, send_from_directory, request
import os
import pandas as pd
from math import ceil
import traceback
import re

app = Flask(__name__, static_folder='.', static_url_path='')

# 每页显示的视频数量
VIDEOS_PER_PAGE = 12

def natural_sort(l):
    """自然排序，确保数字正确排序（1, 2, 10 而不是 1, 10, 2）"""
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)

def get_video_data():
    # 读取Excel文件获取prompt
    try:
        # 列出所有Excel文件，找到最新的一个
        excel_files = [f for f in os.listdir('.') if f.startswith('视频提示词结果_') and f.endswith('.xlsx')]
        if not excel_files:
            print("错误：找不到视频提示词结果Excel文件")
            return []
            
        # 按修改时间排序，获取最新的文件
        latest_excel = sorted(excel_files, key=lambda f: os.path.getmtime(f), reverse=True)[0]
        print(f"使用Excel文件: {latest_excel}")
        
        df = pd.read_excel(latest_excel)
        print(f"成功读取Excel，包含{len(df)}行数据")
        
        # 确认目录存在
        for dir_path in ['results/tongyi', 'results/wavespeed']:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                print(f"创建目录: {dir_path}")
        
        # 使用自然排序获取视频文件列表
        tongyi_videos = natural_sort([f for f in os.listdir('results/tongyi') if f.endswith('.mp4')])
        wavespeed_videos = natural_sort([f for f in os.listdir('results/wavespeed') if f.endswith('.mp4')])
        
        print(f"找到同义视频: {len(tongyi_videos)}个, 文件列表: {tongyi_videos[:5]}...")
        print(f"找到wavespeed视频: {len(wavespeed_videos)}个, 文件列表: {wavespeed_videos[:5]}...")
        
        # 构建映射字典，使用索引作为键
        video_mapping = {}
        
        # 尝试从文件名中提取索引
        for i, filename in enumerate(tongyi_videos):
            # 尝试从文件名中提取索引，假设文件名格式为 "x_tongyi.mp4" 或 "x.mp4"，其中 x 是索引
            match = re.search(r'^(\d+)', filename)
            if match:
                index = int(match.group(1)) - 1  # 减1是因为索引通常从0开始
                if index < len(df):
                    if index not in video_mapping:
                        video_mapping[index] = {'tongyi': filename}
                    else:
                        video_mapping[index]['tongyi'] = filename
        
        for i, filename in enumerate(wavespeed_videos):
            match = re.search(r'^(\d+)', filename)
            if match:
                index = int(match.group(1)) - 1
                if index < len(df):
                    if index not in video_mapping:
                        video_mapping[index] = {'wavespeed': filename}
                    else:
                        video_mapping[index]['wavespeed'] = filename
        
        # 如果没有成功从文件名提取索引，使用简单的顺序匹配
        if not video_mapping:
            print("无法从文件名提取索引，使用顺序匹配")
            for i in range(min(len(tongyi_videos), len(wavespeed_videos), len(df))):
                video_mapping[i] = {
                    'tongyi': tongyi_videos[i] if i < len(tongyi_videos) else None,
                    'wavespeed': wavespeed_videos[i] if i < len(wavespeed_videos) else None
                }
        
        # 构建视频数据
        videos = []
        for index, video_files in sorted(video_mapping.items()):
            if index >= len(df):
                continue
                
            # 获取对应行的提示词
            row = df.iloc[index]
            
            # 优先使用prompt_cn_baidu列，如果不存在则尝试video_prompt
            if 'prompt_cn_baidu' in df.columns and not pd.isna(row['prompt_cn_baidu']):
                prompt_text = str(row['prompt_cn_baidu'])
            elif 'video_prompt' in df.columns and not pd.isna(row['video_prompt']):
                prompt_text = str(row['video_prompt'])
            else:
                prompt_text = "无描述"
                
            # 确保有对应的视频文件
            tongyi_url = f'/results/tongyi/{video_files.get("tongyi")}' if video_files.get("tongyi") else ''
            wavespeed_url = f'/results/wavespeed/{video_files.get("wavespeed")}' if video_files.get("wavespeed") else ''
            
            if tongyi_url and wavespeed_url:
                videos.append({
                    'id': index + 1,
                    'prompt': prompt_text,
                    'tongyi_url': tongyi_url,
                    'wavespeed_url': wavespeed_url
                })
        
        return videos
    except Exception as e:
        print(f"获取视频数据时出错: {str(e)}")
        traceback.print_exc()
        return []

@app.route('/')
def index():
    # 直接发送根目录下的index.html文件，而不是使用render_template
    return send_from_directory('.', 'index.html')

@app.route('/api/videos/<int:page>')
def get_videos(page):
    try:
        videos = get_video_data()
        start_idx = (page - 1) * VIDEOS_PER_PAGE
        end_idx = start_idx + VIDEOS_PER_PAGE
        page_videos = videos[start_idx:end_idx]
        
        return jsonify({
            'videos': page_videos,
            'total_pages': ceil(len(videos) / VIDEOS_PER_PAGE) if videos else 1
        })
    except Exception as e:
        print(f"API错误: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e), 'videos': [], 'total_pages': 1}), 500

@app.route('/results/<path:path>')
def serve_video(path):
    directory, filename = os.path.split(path)
    return send_from_directory(f'results/{directory}', filename)

@app.route('/debug')
def debug_info():
    """返回调试信息"""
    info = {
        'excel_files': [f for f in os.listdir('.') if f.endswith('.xlsx')],
        'tongyi_videos': os.listdir('results/tongyi') if os.path.exists('results/tongyi') else [],
        'wavespeed_videos': os.listdir('results/wavespeed') if os.path.exists('results/wavespeed') else [],
        'current_dir': os.listdir('.')
    }
    return jsonify(info)

if __name__ == '__main__':
    app.run(debug=True, port=5001) 