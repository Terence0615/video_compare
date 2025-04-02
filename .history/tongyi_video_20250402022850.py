import hmac
import time
import requests
from datetime import datetime
import hashlib
import uuid
import base64


class Comfy:
    def __init__(self, ak='-IS1RD71KgHhbRrEkQKUSA', sk='NwNfwchfcHzntMpm2CNzgjTwGXNBHJJb', interval=5):
        """
        :param ak
        :param sk
        :param interval 轮询间隔
        """
        self.ak = ak
        self.sk = sk
        self.time_stamp = int(datetime.now().timestamp() * 1000)  # 毫秒级时间戳
        self.signature_nonce = uuid.uuid1()  # 随机字符串
        self.signature_img = self._hash_sk(self.sk, self.time_stamp, self.signature_nonce)
        self.signature_status = self._hash_sk_status(self.sk, self.time_stamp, self.signature_nonce)
        self.interval = interval
        self.headers = {'Content-Type': 'application/json'}
        self.comfy_url = self.get_image_url(self.ak, self.signature_img, self.time_stamp, self.signature_nonce)
        self.generate_url = self.get_generate_url(self.ak, self.signature_status, self.time_stamp,
                                                  self.signature_nonce)

    def hmac_sha1(self, key, code):
        hmac_code = hmac.new(key.encode(), code.encode(), hashlib.sha1)
        return hmac_code.digest()

    def _hash_sk(self, key, s_time, ro):
        """加密sk"""
        data = "/api/generate/comfyui/app" + "&" + str(s_time) + "&" + str(ro)
        s = base64.urlsafe_b64encode(self.hmac_sha1(key, data)).rstrip(b'=').decode()
        return s

    def _hash_sk_status(self, key, s_time, ro):
        """加密sk"""
        data = "/api/generate/comfy/status" + "&" + str(s_time) + "&" + str(ro)
        s = base64.urlsafe_b64encode(self.hmac_sha1(key, data)).rstrip(b'=').decode()
        return s

    def get_image_url(self, ak, signature, time_stamp, signature_nonce):

        url = f"https://openapi.liblibai.cloud/api/generate/comfyui/app?AccessKey={ak}&Signature={signature}&Timestamp={time_stamp}&SignatureNonce={signature_nonce}"
        return url

    def get_generate_url(self, ak, signature, time_stamp, signature_nonce):

        url = f"https://openapi.liblibai.cloud/api/generate/comfy/status?AccessKey={ak}&Signature={signature}&Timestamp={time_stamp}&SignatureNonce={signature_nonce}"
        return url


    def comfy_app_hunyuanvideo(self):
        """
        混元视频工作流
        """
        base_json = {
            "templateUuid": "4df2efa0f18d46dc9758803e478eb51c",
            "generateParams": {
                "workflowUuid": "844606e8a5d44465a774928d3031fe7f",                
                "30":
                {
                    "class_type": "HyVideoTextEncode",
                    "inputs":
                    {
                        "prompt": "Shoulder camera Angle translation cut in, the morning sun through the curtain wine fall. In the center of the picture is an old man, who is engraving a little wooden dog in front of a woodworking table in a cinematic view. The camera pans in for a close-up of his wrinkled fingers and sawdust. Then the camera orbit around the room, In an old room with a blurred background, woodworking tools are lined up and finished works hang on the walls."
                    }
                }
            }
        }
        self.run(base_json, self.comfy_url)

    def comfy_tongyi_t2v_13b(self,prompt):
        """
        红包工作流
        """
        base_json ={
            "templateUuid": "4df2efa0f18d46dc9758803e478eb51c",
            "generateParams": {
                "60": {
                    "class_type": "SeargePromptText",
                    "inputs": {
                        "prompt": prompt
                    }
                },
                "workflowUuid": "c0261faa1a8b478cacc568293589dbd7"
            }
        }
        self.run(base_json, self.comfy_url)


    def run(self, data, url, timeout=1000):
        """
        发送任务到生图接口，直到返回image为止，失败抛出异常信息
        """
        start_time = time.time()  # 记录开始时间
        # 这里提交任务，校验是否提交成功，并且获取任务ID
        print(url)
        response = requests.post(url=url, headers=self.headers, json=data)
        response.raise_for_status()
        progress = response.json()
        print(progress)

        if progress['code'] == 0:
            # 如果获取到任务ID，执行等待生图
            while True:
                current_time = time.time()
                if (current_time - start_time) > timeout:
                    print(f"{timeout}s任务超时，已退出轮询。")
                    return None

                generate_uuid = progress["data"]['generateUuid']
                data = {"generateUuid": generate_uuid}
                response = requests.post(url=self.generate_url, headers=self.headers, json=data)
                response.raise_for_status()
                progress = response.json()
                print(progress)

                # 检查任务状态
                generate_status = progress['data'].get('generateStatus')
                if generate_status in [6, 7]:
                    print(f"任务失败, 原因：{progress['data'].get('msg')}")
                    return None

                if progress['data'].get('images') and any(
                        image for image in progress['data']['images'] if image is not None):
                    print("任务完成，获取到图像数据。")
                    return progress

                print(f"任务尚未完成，等待 {self.interval} 秒...")
                time.sleep(self.interval)
        else:
            return f'任务失败,原因：code {progress["msg"]}'


def tongyi_generate(prompt):
    test = Comfy()
    start_time = time.time()
    test.comfy_tongyi_t2v_13b(prompt)
    end_time = time.time()
    print("任务耗时：",end_time-start_time)


if __name__ == '__main__':
    prompt = "一个穿着古装的女孩在湖边弹琴，湖水清澈，周围有山有树，远处有炊烟袅袅，女孩弹琴的画面非常唯美。"
    tongyi_generate(prompt)
