import requests
import json
import time

def submit_task(prompt, guidance_scale=5, num_inference_steps=30, 
                size="832*480", enable_safety_checker=True):
    """
    提交图像生成任务
    
    参数:
        prompt (str): 描述想生成的图片
        api_key (str): API密钥
        negative_prompt (str): 负面提示词
        guidance_scale (int): 引导比例
        num_inference_steps (int): 推理步数
        size (str): 图像尺寸
        seed (int): 随机种子
        enable_safety_checker (bool): 是否启用安全检查
        
    返回:
        str: 请求ID，如果失败则返回None
    """

    api_key = "5de29869407db9091464db382269ef941b8d809d22e69dc63aa762a1712d35b5"
    url = "https://api.wavespeed.ai/api/v2/wavespeed-ai/wan-2.1/t2v-480p"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "enable_safety_checker": enable_safety_checker,
        "guidance_scale": guidance_scale,
        "negative_prompt": "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走",
        "num_inference_steps": num_inference_steps,
        "prompt": prompt,
        "seed": -1,
        "size": size
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        result = response.json()
        request_id = result["request_id"]
        print(f"任务提交成功。请求ID: {request_id}")
        return request_id
    else:
        print(f"错误: {response.status_code}, {response.text}")
        return None

def poll_result(request_id, max_attempts=10, sleep_time=1):
    """
    轮询获取任务结果
    
    参数:
        request_id (str): 请求ID
        api_key (str): API密钥
        max_attempts (int): 最大尝试次数
        sleep_time (int): 每次尝试间隔时间(秒)
        
    返回:
        str: 生成的图像URL，如果失败则返回None
    """
    api_key = "5de29869407db9091464db382269ef941b8d809d22e69dc63aa762a1712d35b5"
    url = f"https://api.wavespeed.ai/api/v2/predictions/{request_id}/result"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    attempt = 0
    while attempt < max_attempts:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            status = result.get("status")
            
            if status == "completed":
                image_url = result.get("result", {}).get("urls", [])[0]
                print(f"任务完成。图像URL: {image_url}")
                return image_url
            elif status == "failed":
                print(f"任务失败: {result.get('error')}")
                return None
            else:
                print(f"任务处理中。状态: {status}")
        else:
            print(f"错误: {response.status_code}, {response.text}")
            return None
        
        attempt += 1
        time.sleep(sleep_time)
    
    print(f"达到最大尝试次数 ({max_attempts})，任务未完成")
    return None

def generate_image(prompt, 
                  negative_prompt="", guidance_scale=5, num_inference_steps=30, 
                  size="832*480", seed=-1, enable_safety_checker=True, 
                  max_attempts=10, sleep_time=1):
    """
    生成图像的主函数
    
    参数:
        prompt (str): 描述想生成的图片
        api_key (str): API密钥
        negative_prompt (str): 负面提示词
        guidance_scale (int): 引导比例
        num_inference_steps (int): 推理步数
        size (str): 图像尺寸
        seed (int): 随机种子
        enable_safety_checker (bool): 是否启用安全检查
        max_attempts (int): 最大尝试次数
        sleep_time (int): 每次尝试间隔时间(秒)
        
    返回:
        str: 生成的图像URL，如果失败则返回None
    """
    request_id = submit_task(prompt)
    
    if request_id:
        return poll_result(request_id, max_attempts, sleep_time)
    return None

if __name__ == "__main__":
    # 示例使用
    prompt = "从上方捕捉宁静的秋景，聚焦于水面，水面上有由同心圆形成的柔和涟漪，可能是被阳光折射的。暖色调占主导地位，水和秋叶被描绘成一系列蓝色、橙色和黄色。水面反射出落叶的鲜艳色彩。光、反射和色彩层的复杂相互作用赋予了图像一种抽象、梦幻般的品质。这种艺术与和平的风格培养了一种与自然和谐相处的平静感。关键元素包括反射的水面、排列的光波和秋叶。使用胶片颗粒和反转胶片摄影技术来增强质感和情绪。场景沐浴在温暖的金色光芒中，营造出宁静的绘画氛围。镜头采用俯视角度，捕捉水面细腻的纹理和落叶的倒影。光线透过稀疏的云层，形成斑驳的光影效果，强化了画面的层次感和立体感。通过慢动作镜头，展示涟漪扩散的动态美感，同时保持整体画面的宁静氛围。"
    image_url = generate_image(prompt)
    
    if image_url:
        print(f"成功生成图像: {image_url}")
    else:
        print("图像生成失败")