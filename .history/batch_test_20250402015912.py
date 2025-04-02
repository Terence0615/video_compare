import pandas as pd
import os
from wavespeed import generate_image as wavespeed_generate
from tongyi_video import tongyi_generate
import time
import requests

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

def process_video_prompts():
    # 创建保存目录
    os.makedirs('results/tongyi', exist_ok=True)
    os.makedirs('results/wavespeed', exist_ok=True)
    
    # 读取Excel文件
    df = pd.read_excel('视频提示词结果_20250401_231849.xlsx')
    
    # 处理每个prompt
    for index, row in df.iterrows():
        prompt = row['video_prompt']
        print(f"处理第 {index + 1} 个prompt: {prompt}")
        
        # 生成文件名
        file_prefix = f"video_{index + 1}"
        
        # 调用通义千问API
        try:
            print("正在生成通义千问视频...")
            tongyi_url = tongyi_generate(prompt)
            if tongyi_url:
                tongyi_path = f"results/tongyi/{file_prefix}.mp4"
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
                wavespeed_path = f"results/wavespeed/{file_prefix}.mp4"
                if download_video(wavespeed_url, wavespeed_path):
                    print(f"Wavespeed视频已保存: {wavespeed_path}")
                else:
                    print("Wavespeed视频下载失败")
        except Exception as e:
            print(f"Wavespeed视频生成失败: {str(e)}")
        
        # 等待一段时间再处理下一个，避免API限制
        time.sleep(5)

if __name__ == "__main__":
    process_video_prompts() 