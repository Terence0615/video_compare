import pandas as pd
import os
from wavespeed import generate_image as wavespeed_generate
from tongyi_video import tongyi_generate
import time
import requests
import json
import sys
import io
import subprocess

def setup_console():
    """设置控制台环境"""
    if sys.platform.startswith('win'):
        # 使用subprocess启动新的cmd窗口
        if not os.environ.get('PYTHONIOENCODING'):
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            # 重新启动脚本
            subprocess.run(['cmd', '/c', 'python', __file__], 
                         creationflags=subprocess.CREATE_NEW_CONSOLE)
            sys.exit()

def download_video(url, save_path):
    """下载视频到指定路径"""
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    return False

def load_processed_prompts():
    """加载已处理的prompt记录"""
    if os.path.exists('processed_prompts.json'):
        with open('processed_prompts.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_processed_prompts(processed_data):
    """保存已处理的prompt记录"""
    with open('processed_prompts.json', 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)

def check_video_exists(file_path):
    """检查视频文件是否存在且有效"""
    if not os.path.exists(file_path):
        return False
    # 检查文件大小是否大于1KB（避免空文件）
    return os.path.getsize(file_path) > 1024

def process_video_prompts():
    # 创建保存目录
    os.makedirs('results/tongyi', exist_ok=True)
    os.makedirs('results/wavespeed', exist_ok=True)
    
    # 加载已处理的prompt记录
    processed_prompts = load_processed_prompts()
    
    # 读取Excel文件
    df = pd.read_excel('视频提示词结果_20250401_231849.xlsx')
    
    # 处理每个prompt
    for index, row in df.iterrows():
        prompt = row['video_prompt']
        print(f"处理第 {index + 1} 个prompt: {prompt}")
        
        # 生成文件名
        file_prefix = f"video_{index + 1}"
        tongyi_path = f"results/tongyi/{file_prefix}.mp4"
        wavespeed_path = f"results/wavespeed/{file_prefix}.mp4"
        
        # 检查是否已经处理过这个prompt
        if str(index) in processed_prompts:
            # 检查视频文件是否存在且有效
            if (check_video_exists(tongyi_path) and 
                check_video_exists(wavespeed_path)):
                print(f"视频 {file_prefix} 已存在，跳过处理")
                continue
            else:
                print(f"视频 {file_prefix} 文件无效或不存在，重新处理")
        
        # 调用通义千问API
        try:
            print("正在生成通义千问视频...")
            tongyi_url = tongyi_generate(prompt)
            if tongyi_url:
                if download_video(tongyi_url, tongyi_path):
                    print(f"通义千问视频已保存: {tongyi_path}")
                else:
                    print("通义千问视频下载失败")
        except Exception as e:
            print(f"通义千问视频生成失败: {str(e)}")
        
        # 调用Wavespeed API
        try:
            print("正在生成Wavespeed视频...")
            wavespeed_url = wavespeed_generate(prompt)
            if wavespeed_url:
                if download_video(wavespeed_url, wavespeed_path):
                    print(f"Wavespeed视频已保存: {wavespeed_path}")
                else:
                    print("Wavespeed视频下载失败")
        except Exception as e:
            print(f"Wavespeed视频生成失败: {str(e)}")
        
        # 记录处理成功的prompt
        if check_video_exists(tongyi_path) and check_video_exists(wavespeed_path):
            processed_prompts[str(index)] = {
                'prompt': prompt,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'tongyi_path': tongyi_path,
                'wavespeed_path': wavespeed_path
            }
            save_processed_prompts(processed_prompts)
        
        # 等待一段时间再处理下一个，避免API限制
        time.sleep(5)

if __name__ == "__main__":
    setup_console()
    process_video_prompts() 