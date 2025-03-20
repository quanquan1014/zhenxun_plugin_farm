from zhenxun.services.log import logger
from zhenxun.utils._build_image import BuildImage
from zhenxun.utils.image_utils import ImageTemplate

from ..config import g_pJsonManager, g_sResourcePath
from ..database import g_pSqlManager


class CShopManager:

    @classmethod
    async def getSeedShopImage(cls) -> bytes:
        """获取商店页面

        TODO: 缺少翻页功能

        Returns:
            bytes: 返回商店图片bytes
        """

        data_list = []
        column_name = [
            "-",
            "种子名称",
            "解锁等级",
            "种子单价",
            "收获经验",
            "收获数量",
            "成熟时间（小时）",
            "收获次数",
            "再次成熟时间（小时）",
            "是否可以上架交易行"
        ]

        sell = ""
        plants = g_pJsonManager.m_pPlant['plant'] # type: ignore
        for key, plant in plants.items():
            icon = ""
            icon_path = g_sResourcePath / f"plant/{key}/icon.png"
            if icon_path.exists():
                icon = (icon_path, 33, 33)

            if plant['again'] == True:
                sell = "可以"
            else:
                sell = "不可以"

            data_list.append(
                [
                    icon,
                    key,
                    plant['level'],
                    plant['price'],
                    plant['experience'],
                    plant['harvest'],
                    plant['time'],
                    plant['crop'],
                    plant['again'],
                    sell
                ]
            )

        result = await ImageTemplate.table_page(
            "种子商店",
            "购买示例：@小真寻 购买种子 大白菜 5",
            column_name,
            data_list,
        )

        return result.pic2bytes()

    @classmethod
    async def buySeed(cls, uid: str, name: str, num: int = 1) -> str:
        """购买种子

        Args:
            uid (str): 用户Uid
            name (str): 植物名称
            num (int, optional): 购买数量

        Returns:
            str:
        """

        if num <= 0:
            return "请输入购买数量！"

        plantInfo = None

        try:
            plantInfo = g_pJsonManager.m_pPlant['plant'][name] # type: ignore
        except Exception as e:
            return "购买出错！请检查需购买的种子名称！"

        userPlants = {}

        point = await g_pSqlManager.getUserPointByUid(uid)
        total = int(plantInfo['price']) * num

        logger.debug(f"用户：{uid}购买{name}，数量为{num}。用户农场币为{point}，购买需要{total}")

        if point < total:
            return "你的农场币不够哦~ 快速速氪金吧！"
        else:
            p = await g_pSqlManager.getUserSeedByUid(uid)

            if not p == None:
                for item in p.split(','):
                    if '|' in item:
                        plant_name, count = item.split('|', 1)  # 分割一次，避免多竖线问题
                        userPlants[plant_name] = int(count)

            if name in userPlants:
                userPlants[name] += num
            else:
                userPlants[name] = num

            plantList = [f"{k}|{v}" for k, v in userPlants.items()]

            await g_pSqlManager.updateUserPointByUid(uid, point - total)
            await g_pSqlManager.updateUserSeedByUid(uid, ','.join(plantList))

            return f"成功购买{name}，当前仓库数量为：{userPlants[name]}，花费{total}农场币, 剩余{point - total}农场币"


g_pShopManager = CShopManager()
