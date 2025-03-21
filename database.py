import os
from datetime import date, datetime, timedelta
from io import StringIO
from math import e
from typing import Any, List, Optional

import aiosqlite

from zhenxun.services.log import logger

from .config import g_pJsonManager, g_sDBFilePath, g_sDBPath


class CSqlManager:
    def __init__(self):
        g_sDBPath.mkdir(parents=True, exist_ok=True)

    @classmethod
    async def cleanup(cls):
        if cls.m_pDB:
            await cls.m_pDB.close()
            cls.m_pDB = None

    @classmethod
    async def init(cls) -> bool:
        bIsExist = os.path.exists(g_sDBFilePath)

        cls.m_pDB = await aiosqlite.connect(g_sDBFilePath)

        if bIsExist == False:
            # TODO 缺少判断创建失败事件
            await cls.createDB()

        return True

    @classmethod
    async def createDB(cls) -> bool:
        """初始化数据库用户信息表

        Returns:
            bool: 是否创建成功
        """

        #用户信息
        userInfo =  """
            CREATE TABLE user (
                uid INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                exp INTEGER DEFAULT 0,
                point INTEGER DEFAULT 0,
                soil INTEGER DEFAULT 3,
                stealing TEXT DEFAULT NULL
            );
            """

        #用户仓库
        userStorehouse =  """
            CREATE TABLE storehouse (
                uid INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT DEFAULT '',
                plant TEXT DEFAULT '',
                seed TEXT DEFAULT ''
            );
            """

        #用户土地信息
        with StringIO() as buffer:
            buffer.write("CREATE TABLE soil (")
            buffer.write("uid INTEGER PRIMARY KEY AUTOINCREMENT,")

            fields = [f"soil{i} TEXT DEFAULT ''" for i in range(1, 31)]
            buffer.write(",\n".join(fields))

            buffer.write(");")

            userSoilInfo = buffer.getvalue()

        if not await cls.executeDB(userInfo):
            return False

        if not await cls.executeDB(userStorehouse):
            return False

        if not await cls.executeDB(userSoilInfo):
            return False

        return True

    @classmethod
    async def executeDB(cls, command: str) -> bool:
        """执行自定义SQL

        Args:
            command (str): SQL语句

        Returns:
            bool: 是否执行成功
        """

        if len(command) <= 0:
            logger.warning("数据库语句长度不能！")
            return False

        try:
            await cls.m_pDB.execute(command)
            await cls.m_pDB.commit()
            return True
        except Exception as e:
            logger.warning("数据库语句执行出错：" + command)
            return False

    @classmethod
    async def initUserInfoByUid(cls, uid: str, name: str = "", exp: int = 0, point: int = 100):
        """初始化用户信息

        Args:
            uid (str): 用户Uid
            name (str): 农场名称
            exp (int): 农场经验
            point (int): 农场币
        """

        #用户信息
        userInfo =  f"""
            INSERT INTO user (uid, name, exp, point, soil, stealing) VALUES ({uid}, '{name}', {exp}, {point}, 3, '{date.today()}|5')
            """

        #用户仓库
        userStorehouse = f"""
            INSERT INTO storehouse (uid) VALUES ({uid});
            """

        #用户土地
        userSoilInfo = f"""
            INSERT INTO soil (uid) VALUES ({uid});
            """

        if not await cls.executeDB(userInfo):
            return False

        if not await cls.executeDB(userStorehouse):
            return False

        if not await cls.executeDB(userSoilInfo):
            return False

        return "开通农场成功"

    @classmethod
    async def getUserInfoByUid(cls, uid: str) -> dict:
        """根据用户Uid获取用户信息

        Args:
            uid (str): 用户Uid

        Returns:
            list[dict]: 用户信息
        """
        if len(uid) <= 0:
            return {}

        try:
            async with cls.m_pDB.execute(
                "SELECT * FROM user WHERE uid = ?", (uid,)
            ) as cursor:
                async for row in cursor:
                    userDict = {
                        "uid": row[0],
                        "name": row[1],
                        "exp": row[2],
                        "point": row[3],
                        "soil": row[4],
                        "stealing": row[5]
                    }

                    return userDict
            return {}
        except Exception as e:
            logger.warning(f"getUserInfoByUid查询失败: {e}")
            return {}

    @classmethod
    async def getUserPointByUid(cls, uid: str) -> int:
        """根据用户Uid获取用户农场币

        Args:
            uid (str): 用户Uid

        Returns:
            int: 用户农场币
        """
        if len(uid) <= 0:
            return -1

        try:
            async with cls.m_pDB.execute(
                f"SELECT point FROM user WHERE uid = {uid}"
            ) as cursor:
                async for row in cursor:
                    return int(row[0])

            return -1
        except Exception as e:
            logger.warning(f"getUserPointByUid查询失败: {e}")
            return -1

    @classmethod
    async def updateUserPointByUid(cls, uid: str, point: int) -> int:
        """根据用户Uid修改用户农场币

        Args:
            uid (str): 用户Uid
            point (int): 要更新的新农场币数量（需 ≥ 0）

        Returns:
            int: 更新后的农场币数量（成功时），-1（失败时）
        """

        if len(uid) <= 0:
            logger.warning("参数校验失败: uid为空或农场币值无效")
            return -1

        try:
            async with cls.m_pDB.execute(f"UPDATE user SET point = {point} WHERE uid = '{uid}'") as cursor:
                async for row in cursor:
                    return int(row[0])

            logger.info(f"未找到用户或未修改数据: uid={uid}")
            return -1
        except Exception as e:
            # 记录详细错误日志（建议记录堆栈）
            logger.error(f"金币更新失败: {e}")
            return -1

    @classmethod
    async def getUserExpByUid(cls, uid: str) -> int:
        """根据用户Uid获取用户经验

        Args:
            uid (str): 用户Uid

        Returns:
            int: 用户经验值
        """
        if len(uid) <= 0:
            return -1

        try:
            async with cls.m_pDB.execute(f"SELECT exp FROM user WHERE uid = '{uid}'") as cursor:
                async for row in cursor:
                    return int(row[0])

            return -1
        except Exception as e:
            logger.warning(f"getUserLevelByUid查询失败: {e}")
            return -1

    @classmethod
    async def UpdateUserExpByUid(cls, uid: str, exp: int) -> bool:
        """根据用户Uid刷新用户经验

        Args:
            uid (str): 用户Uid

        Returns:
            bool: 是否成功
        """
        if len(uid) <= 0:
            return False

        sql = f"UPDATE user SET exp = '{exp}' WHERE uid = '{uid}'"

        return await cls.executeDB(sql)

    @classmethod
    async def getUserLevelByUid(cls, uid: str) -> int:
        """根据用户Uid获取用户等级

        Args:
            uid (str): 用户Uid

        Returns:
            int: 用户等级`
        """
        if len(uid) <= 0:
            return -1

        try:
            async with cls.m_pDB.execute(f"SELECT exp FROM user WHERE uid = '{uid}'") as cursor:
                async for row in cursor:
                    exp = int(row[0])

                    #获取等级列表
                    levelDict = g_pJsonManager.m_pLevel['level'] # type: ignore

                    sorted_keys = sorted(levelDict.keys(), key=lambda x: int(x), reverse=True)
                    for key in sorted_keys:
                        if exp >= levelDict[key]:
                            return int(key)

            return -1
        except Exception as e:
            logger.warning(f"getUserLevelByUid查询失败: {e}")
            return -1

    @classmethod
    async def getUserSoilByUid(cls, uid: str) -> int:
        """根据用户Uid获取解锁地块

        Args:
            uid (str): 用户Uid

        Returns:
            int: 解锁几块地
        """
        if len(uid) <= 0:
            return 0

        async with cls.m_pDB.execute(f"SELECT soil FROM user WHERE uid = '{uid}'") as cursor:
            async for row in cursor:
                if not row[0]:
                    return 0
                else:
                    return int(row[0])

        return 0

    @classmethod
    async def getUserSoilStatusBySoilID(cls, uid: str, soil: str) -> tuple[bool, str]:
        """根据土地块获取用户土地状态

        Args:
            uid (str): 用户Uid
            soil (str): 土地id

        Returns:
            tuple[bool, str]: [是否可以播种，土地信息]
        """
        if len(uid) <= 0:
            return False, ""

        async with cls.m_pDB.execute(f"SELECT {soil} FROM soil WHERE uid = '{uid}'") as cursor:
            async for row in cursor:
                if row[0] == None or len(row[0]) <= 0:
                    return True, ""
                else:
                    return False, row[0]

        return False, ""

    @classmethod
    async def updateUserSoilStatusByPlantName(cls, uid: str, soil: str,
                                              plant: str = "",
                                              status: int = 0) -> bool:
        """根据种子名称使用户播种

        Args:
            uid (str): 用户Uid
            soil (str): 土地id
            plant (str): 种子名称

        Returns:
            bool: 是否更新成功
        """

        if len(uid) <= 0:
            return False

        if len(plant) <= 0 and status == 4:
            s = f",,,{status},"
        elif len(plant) <= 0 and status != 4:
            s = ""
        else:
            #获取种子信息 这里能崩我吃
            plantInfo = g_pJsonManager.m_pPlant['plant'][plant] # type: ignore

            currentTime = datetime.now()
            newTime = currentTime + timedelta(minutes=int(plantInfo['time']))

            #种子名称，种下时间，预计成熟时间，地状态：0：无 1：长草 2：生虫 3：缺水 4：枯萎，是否被偷 示例：QQ号-偷取数量|QQ号-偷取数量
            s = f"{plant},{int(currentTime.timestamp())},{int(newTime.timestamp())},{status},"

        sql = f"UPDATE soil SET {soil} = '{s}' WHERE uid = '{uid}'"

        return await cls.executeDB(sql)

    @classmethod
    async def getUserSeedByUid(cls, uid: str) -> str:
        """获取用户仓库种子信息

        Args:
            info (list[dict]): 用户信息

        Returns:
            str: 仓库种子信息
        """

        if len(uid) <= 0:
            return ""

        try:
            async with cls.m_pDB.execute(f"SELECT seed FROM storehouse WHERE uid = '{uid}'") as cursor:
                async for row in cursor:
                    return row[0]

            return ""
        except Exception as e:
            logger.warning(f"getUserSeedByUid查询失败: {e}")
            return ""

    @classmethod
    async def updateUserSeedByUid(cls, uid: str, seed: str) -> bool:
        """更新用户种子仓库

        Args:
            uid (str): 用户Uid
            seed (str): 种子名称

        Returns:
            bool:
        """

        if len(uid) <= 0:
            return False

        sql = f"UPDATE storehouse SET seed = '{seed}' WHERE uid = '{uid}'"

        return await cls.executeDB(sql)

    @classmethod
    async def getUserPlantByUid(cls, uid: str) -> str:
        """获取用户仓库作物信息

        Args:
            info (list[dict]): 用户信息

        Returns:
            str: 仓库作物信息
        """

        if len(uid) <= 0:
            return ""

        try:
            async with cls.m_pDB.execute(f"SELECT plant FROM storehouse WHERE uid = '{uid}'") as cursor:
                async for row in cursor:
                    return row[0]

            return ""
        except Exception as e:
            logger.warning(f"getUserPlantByUid查询失败: {e}")
            return ""

    @classmethod
    async def updateUserPlantByUid(cls, uid: str, plant: str) -> bool:
        """更新用户作物仓库

        Args:
            uid (str): 用户Uid
            plant (str): 作物名称

        Returns:
            bool:
        """

        if len(uid) <= 0:
            return False

        sql = f"UPDATE storehouse SET plant = '{plant}' WHERE uid = '{uid}'"

        return await cls.executeDB(sql)

g_pSqlManager = CSqlManager()
