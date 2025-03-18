from zhenxun.services.log import logger
from zhenxun.utils._build_image import BuildImage

from ..config import g_pJsonManager, g_sResourcePath
from ..database import g_pSqlManager


class CShopManager:

    @classmethod
    async def getPlantShopImage(cls) -> bytes:
        return bytes()

    @classmethod
    async def buyPlant(cls, uid: str, name: str, num: int = 1) -> str:
        if num <= 0:
            return "请输入购买数量！"

        plants = g_pJsonManager.m_pPlant['plant'] # type: ignore

        for key, plant in plants.items():
            if plant['name'] == name:
                point = g_pSqlManager.getUserPointByUid(uid)
                total = int(plant['price']) * num

                if point < total
                    return "你的农场币不够哦~ 快速速氪金吧！"
                else:
                    await g_pSqlManager.updateUserPointByUid(uid, point - total)

        pass