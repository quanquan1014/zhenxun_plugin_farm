from unittest import result

import requests


class CRequestManager:

    @classmethod
    async def post(cls, url, json_data=None, form_data=None):
        """发送 POST 请求（支持 JSON/Form-Data 格式）"""
        try:
            headers = {"Content-Type": "application/json"} if json_data else None
            response = requests.post(
                url,
                json=json_data,
                data=form_data,
                headers=headers,
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            return {}

    @classmethod
    async def sign(cls, uid: str) -> str:
        a = await cls.post("http://diuse.work:9099/testPost", json_data={"level":3})

        result = ""
        if int(a["type"]) == 1:
            result = f"签到成功"

        return result


g_pRequestManager = CRequestManager()
