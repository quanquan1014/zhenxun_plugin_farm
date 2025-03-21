import asyncio
import random
from datetime import date, datetime
from io import StringIO
from typing import Dict, List, Tuple

from zhenxun.models.user_console import UserConsole
from zhenxun.services.log import logger
from zhenxun.utils._build_image import BuildImage
from zhenxun.utils.enum import GoldHandle
from zhenxun.utils.image_utils import ImageTemplate

from ..config import g_pJsonManager, g_sResourcePath
from ..database import g_pSqlManager


class CFarmManager:
    @classmethod
    async def buyPointByUid(cls, uid: str, num: int) -> str:
        if num <= 0:
            return "你是怎么做到购买不是正数的农场币的"

        user = await UserConsole.get_user(uid)

        point = num // 2

        if user.gold < point:
            return "你的金币不足"

        await UserConsole.reduce_gold(uid, point, GoldHandle.BUY , 'zhenxun_plugin_farm')

        p = await g_pSqlManager.getUserPointByUid(uid)

        await g_pSqlManager.updateUserPointByUid(uid, num + p)

        return f"充值{num}农场币成功，当前农场币：{num + p}"

    @classmethod
    async def drawFarmByUid(cls, uid: str) -> bytes:
        """绘制用户农场

        Args:
            uid (str): 用户UID

        Returns:
            bytes: 返回绘制结果
        """
        soilNumber = await g_pSqlManager.getUserLevelByUid(uid)

        img = BuildImage(background = g_sResourcePath / "background/background.jpg")

        soilSize = g_pJsonManager.m_pSoil['size'] # type: ignore

        #TODO 缺少判断用户土地资源状况
        soil = BuildImage(background = g_sResourcePath / "soil/普通土地.png")
        await soil.resize(0, soilSize[0], soilSize[1])

        grass = BuildImage(background = g_sResourcePath / "soil/草土地.png")
        await grass.resize(0, soilSize[0], soilSize[1])

        soilPos = g_pJsonManager.m_pSoil['soil'] # type: ignore
        soilUnlock = await g_pSqlManager.getUserSoilByUid(uid)

        x = 0
        y = 0
        isFirstExpansion = True #首次添加扩建图片
        isFirstRipe = True
        plant = None
        for index in range(0, 30):
            x = soilPos[str(index + 1)]['x']
            y = soilPos[str(index + 1)]['y']

            #如果土地已经到达对应等级
            if index < soilUnlock:
                await img.paste(soil, (x, y))

                isPlant, plant, isRipe= await cls.drawSoilPlant(uid, f"soil{str(index + 1)}")

                if isPlant:
                    await img.paste(plant, (x + soilSize[0] // 2 - plant.width // 2,
                                            y + soilSize[1] // 2 - plant.height // 2))

                #首次添加可收获图片
                if isRipe and isFirstRipe:
                    ripe = BuildImage(background = g_sResourcePath / "background/ripe.png")

                    await img.paste(ripe, (x + soilSize[0] // 2 - ripe.width // 2,
                                           y - ripe.height // 2))

                    isFirstRipe = False
            else:
                await img.paste(grass, (x, y))

                if isFirstExpansion:
                    isFirstExpansion = False

                    #首次添加扩建图片
                    expansion = BuildImage(background = g_sResourcePath / "background/expansion.png")
                    await expansion.resize(0, 69, 69)
                    await img.paste(expansion, (x + soilSize[0] // 2 - expansion.width // 2,
                                                y + soilSize[1] // 2 - expansion.height))

        await img.resize(0.6)
        return img.pic2bytes()

    @classmethod
    async def drawSoilPlant(cls, uid: str, soilid: str) -> tuple[bool, BuildImage, bool]:
        """绘制植物资源

        Args:
            uid (str): 用户Uid
            soilid (str): 土地id

        Returns:
            tuple[bool, BuildImage]: [绘制是否成功，资源图片, 是否成熟]
        """

        plant = None
        soilStatus, soilInfo = await g_pSqlManager.getUserSoilStatusBySoilID(uid, soilid)

        if soilStatus == True:
            return False, None, False
        else:
            soilInfo = soilInfo.split(',')

            if int(soilInfo[3]) == 4:
                plant = BuildImage(background = g_sResourcePath / f"plant/basic/9.png")
                await plant.resize(0, 150, 212)
                return True, plant, False

            plantInfo = g_pJsonManager.m_pPlant['plant'][soilInfo[0]]  # type: ignore

            currentTime = datetime.now()
            matureTime = datetime.fromtimestamp(int(soilInfo[2]))

            if currentTime >= matureTime:
                phase = int(plantInfo['phase'])
                plant = BuildImage(background = g_sResourcePath / f"plant/{soilInfo[0]}/{phase - 1}.png")

                return True, plant, True
            else:
                plantedTime = datetime.fromtimestamp(int(soilInfo[1]))

                elapsedTime = currentTime - plantedTime
                elapsedHour = elapsedTime.total_seconds() / 60 / 60

                currentStage = int(elapsedHour / (plantInfo['time'] / (plantInfo['phase'] - 1)))

                #TODO 缺少判断部分种子是否是通用0阶段图片
                if currentStage <= 0:
                    plant = BuildImage(background = g_sResourcePath / f"plant/basic/0.png")
                    await plant.resize(0, 35, 58)
                else:
                    plant = BuildImage(background = g_sResourcePath / f"plant/{soilInfo[0]}/{currentStage}.png")

        return True, plant, False

    @classmethod
    async def getUserSeedByUid(cls, uid: str) -> bytes:
        """获取用户种子仓库

        Args:
            uid (str): 用户Uid

        Returns:
            bytes: 返回图片
        """

        data_list = []
        column_name = [
            "-",
            "种子名称",
            "数量",
            "收获经验",
            "收获数量",
            "成熟时间（小时）",
            "收获次数",
            "再次成熟时间（小时）",
            "是否可以上架交易行"
        ]

        seed = await g_pSqlManager.getUserSeedByUid(uid)

        if seed == None:
            result = await ImageTemplate.table_page(
                "种子仓库",
                "播种示例：@小真寻 播种 大白菜 [数量]",
                column_name,
                data_list,
            )

            return result.pic2bytes()

        sell = ""
        for item in seed.split(','):
            if '|' in item:
                seedName, count = item.split('|', 1)  # 分割一次，避免多竖线问题
                try:
                    plantInfo = g_pJsonManager.m_pPlant['plant'][seedName] # type: ignore

                    icon = ""
                    icon_path = g_sResourcePath / f"plant/{seedName}/icon.png"
                    if icon_path.exists():
                        icon = (icon_path, 33, 33)

                    if plantInfo['again'] == True:
                        sell = "可以"
                    else:
                        sell = "不可以"

                    data_list.append(
                        [
                            icon,
                            seedName,
                            count,
                            plantInfo['experience'],
                            plantInfo['harvest'],
                            plantInfo['time'],
                            plantInfo['crop'],
                            plantInfo['again'],
                            sell
                        ]
                    )

                except Exception as e:
                    continue

        result = await ImageTemplate.table_page(
            "种子仓库",
            "播种示例：@小真寻 播种 大白菜 [数量]",
            column_name,
            data_list,
        )

        return result.pic2bytes()

    @classmethod
    async def sowing(cls, uid: str, name: str, num: int = -1) -> str:
        """播种

        Args:
            uid (str): 用户Uid
            name (str): 播种种子名称
            num (int, optional): 播种数量

        Returns:
            str:
        """
        plant = await g_pSqlManager.getUserSeedByUid(uid)

        if plant == None:
            return "你的种子仓库是空的，快去买点吧！"

        plantDict = {}
        for item in plant.split(','):
            if '|' in item:
                seed_name, count = item.split('|', 1)
                plantDict[seed_name] = int(count)

        isAll = False
        if num == -1:
            isAll = True

        soilNumber = await g_pSqlManager.getUserSoilByUid(uid)

        for i in range(1, soilNumber + 1):
            if plantDict[name] > 0:
                if isAll or num > 0:
                    soilName = f"soil{i}"
                    success, message = await g_pSqlManager.getUserSoilStatusBySoilID(uid, soilName)
                    if success:
                        # 更新种子数量
                        num -= 1
                        plantDict[name] -= 1

                        # 更新数据库
                        await g_pSqlManager.updateUserSoilStatusByPlantName(uid, soilName, name)

        await g_pSqlManager.updateUserSeedByUid(
            uid,
            ','.join([f"{k}|{v}" for k, v in plantDict.items()])
        )

        if num > 0:
            return f"播种数量超出开垦土地数量，已将可播种土地成功播种{name}！仓库还剩下{plantDict[name]}个种子"
        else:
            return f"播种{name}成功！仓库还剩下{plantDict[name]}个种子"

    @classmethod
    async def harvest(cls, uid: str) -> str:
        """收获作物

        Args:
            uid (str): 用户Uid

        Returns:
            str: 返回
        """

        soilUnlock = await g_pSqlManager.getUserSoilByUid(uid)

        plant = {}

        soilNames = [f"soil{i}" for i in range(soilUnlock)]
        soilStatuses = await asyncio.gather(*[
            g_pSqlManager.getUserSoilStatusBySoilID(uid, name)
            for name in soilNames
        ])

        plant: Dict[str, int] = {}
        harvestRecords: List[str] = []
        experience = 0

        for (soil_name, (status, info)) in zip(soilNames, soilStatuses):
            if not status:
                soilInfo = info.split(',')
                plantId = soilInfo[0]
                plantInfo = g_pJsonManager.m_pPlant['plant'][plantId]  # type: ignore

                currentTime = datetime.now()
                matureTime = datetime.fromtimestamp(int(soilInfo[2]))

                if currentTime >= matureTime:
                    number = plantInfo['harvest']

                    #判断该土地作物是否被透过
                    if len(soilInfo[4]) > 0:
                        stealingStatus = soilInfo[4].split('|')
                        for isUser in stealingStatus:
                            user = isUser.split('-')
                            number -= user[1]

                    plant[plantId] = plant.get(plantId, 0) + number
                    experience += plantInfo['experience']
                    harvestRecords.append(f"收获作物：{plantId}，数量为：{number}，经验为：{plantInfo['experience']}")

                    #批量更新数据库操作
                    await g_pSqlManager.updateUserSoilStatusByPlantName(uid, soil_name, "", 4)

        if experience > 0:
            harvestRecords.append(f"\t累计获得经验：{experience}")
            exp = await g_pSqlManager.getUserExpByUid(uid)
            await g_pSqlManager.UpdateUserExpByUid(uid, exp + experience)

        if not plant:
            return "可收获作物为0哦~ 不要试图拔苗助长"
        else:
            # 批量更新用户作物数据
            await g_pSqlManager.updateUserPlantByUid(
                uid,
                ','.join([f"{k}|{v}" for k, v in plant.items()])
            )

            return "\n".join(harvestRecords)

    @classmethod
    async def eradicate(cls, uid: str) -> str:
        """铲除作物
        TODO 缺少随意铲除作物 目前只能铲除荒废作物
        Args:
            uid (str): 用户Uid

        Returns:
            str: 返回
        """

        soilUnlock = await g_pSqlManager.getUserSoilByUid(uid)

        soilNames = [f"soil{i}" for i in range(soilUnlock)]
        soilStatuses = await asyncio.gather(*[
            g_pSqlManager.getUserSoilStatusBySoilID(uid, name)
            for name in soilNames
        ])

        experience = 0
        for (soil_name, (status, info)) in zip(soilNames, soilStatuses):
            if not status:
                soilInfo = info.split(',')
                if int(soilInfo[3]) == 4:
                    experience += 3

                    # 批量更新数据库操作
                    await g_pSqlManager.updateUserSoilStatusByPlantName(uid, soil_name, "", 0)

        if experience > 0:
            exp = await g_pSqlManager.getUserExpByUid(uid)
            await g_pSqlManager.UpdateUserExpByUid(uid, exp + experience)

            return f"成功铲除荒废作物，累计获得经验：{experience}"
        else:
            return "没有可以铲除的作物"

    @classmethod
    async def getUserPlantByUid(cls, uid: str) -> bytes:
        """获取用户作物仓库

        Args:
            uid (str): 用户Uid

        Returns:
            bytes: 返回图片
        """

        data_list = []
        column_name = [
            "-",
            "作物名称",
            "数量",
            "单价",
            "总价",
            "是否可以上架交易行"
        ]

        plant = await g_pSqlManager.getUserPlantByUid(uid)

        if plant == None:
            result = await ImageTemplate.table_page(
                "作物仓库",
                "播种示例：@小真寻 出售作物 大白菜 [数量]",
                column_name,
                data_list,
            )

            return result.pic2bytes()

        sell = ""
        for item in plant.split(','):
            if '|' in item:
                plantName, count = item.split('|', 1)  # 分割一次，避免多竖线问题
                try:
                    plantInfo = g_pJsonManager.m_pPlant['plant'][plantName] # type: ignore

                    icon = ""
                    icon_path = g_sResourcePath / f"plant/{plantName}/icon.png"
                    if icon_path.exists():
                        icon = (icon_path, 33, 33)

                    if plantInfo['again'] == True:
                        sell = "可以"
                    else:
                        sell = "不可以"

                    number = int(count) * plantInfo['price']

                    data_list.append(
                        [
                            icon,
                            plantName,
                            count,
                            plantInfo['price'],
                            number,
                            sell
                        ]
                    )

                except Exception as e:
                    continue

        result = await ImageTemplate.table_page(
            "作物仓库",
            "播种示例：@小真寻 出售作物 大白菜 [数量]",
            column_name,
            data_list,
        )

        return result.pic2bytes()

    @classmethod
    async def stealing(cls, uid: str, target: str) -> str:
        """偷菜

        Args:
            uid (str): 用户Uid
            target (str): 被偷用户Uid

        Returns:
            str: 返回
        """

        #用户信息
        userInfo = await g_pSqlManager.getUserInfoByUid(uid)
        #用户可偷次数
        userStealing = userInfo["stealing"].split('|')

        if date.fromisoformat(userStealing[0]) != date.today():
            userStealing[0] = date.today()
            userStealing[1] = 5

        if int(userStealing[1]) <= 0:
            return "你今天可偷次数到达上限啦，手下留情吧"

        #获取用户
        soilUnlock = int(userInfo["soil"])

        plant = {}

        #根据解锁土地，获取每块土地状态信息
        soilNames = [f"soil{i}" for i in range(soilUnlock)]
        soilStatuses = await asyncio.gather(*[
            g_pSqlManager.getUserSoilStatusBySoilID(target, name)
            for name in soilNames
        ])

        plant: Dict[str, int] = {}
        harvestRecords: List[str] = []

        isStealing = False
        for(soilName, (status, info)) in zip(soilNames, soilStatuses):
            isStealing = False

            if not status:
                soilInfo = info.split(',')
                plantId = soilInfo[0]
                plantInfo = g_pJsonManager.m_pPlant['plant'][plantId]  # type: ignore

                currentTime = datetime.now()
                matureTime = datetime.fromtimestamp(int(soilInfo[2]))

                stealingNumber = 0

                if currentTime >= matureTime:
                    #先获取用户是否偷过该土地
                    stealingStatus = soilInfo[4].split('|')
                    for isUser in stealingStatus:
                        user = isUser.split('-')

                        if user[0] == uid:
                            isStealing = True
                            break

                        stealingNumber += int(user[1])

                    #如果偷过，则跳过该土地
                    if isStealing:
                        continue

                    stealingNumber -= plantInfo['harvest']
                    randomNumber = random.choice([1, 2])
                    randomNumber = min(randomNumber, stealingNumber)

                    if randomNumber > 0:
                        plant[plantId] = plant.get(plantId, 0) + randomNumber
                        harvestRecords.append(f"成功偷到作物：{plantId}，数量为：{randomNumber}")

                        stealingStatus += f"|{uid}-{randomNumber}"

                        #如果将作物偷完，就直接更新状态 并记录用户偷取过
                        if plantInfo['harvest'] - randomNumber + stealingNumber == 0:
                            sql = f"UPDATE soil SET {soilName} = ',,,4,{stealingStatus}' WHERE uid = '{target}'"
                        else:
                            sql = f"UPDATE soil SET {soilName} = '{soilInfo[0]},{soilInfo[1]},{soilInfo[2]},{soilInfo[3]},{stealingStatus}' WHERE uid = '{target}'"

                        await g_pSqlManager.executeDB(sql)

        if not plant:
            return "目标没有作物可以被偷"
        else:
            # 批量更新用户作物仓库数据
            await g_pSqlManager.updateUserPlantByUid(target, ','.join([f"{k}|{v}" for k, v in plant.items()]))

            userStealing[1] = int(userStealing[1]) - 1

            sql = f"UPDATE user SET stealing = {'|'.join(userStealing)} WHERE uid = {uid}"

            #更新用户每日偷取次数
            await g_pSqlManager.executeDB(sql)

            return "\n".join(harvestRecords)

    # @classmethod
    # async def reclamation(cls, uid: str) -> str:

    #     userInfo = await g_pSqlManager.getUserInfoByUid(uid)
    #     level = await g_pSqlManager.getUserLevelByUid(uid)

    #     rec = g_pJsonManager["reclamation"]  # type: ignore

    #     if not rec[f"{userInfo["soil"] + 1}"] == None

    #     return ""

g_pFarmManager = CFarmManager()
