import os
from datetime import datetime, timedelta
from io import StringIO
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
                point INTEGER DEFAULT 0
            );
            """

        #用户仓库
        userStorehouse =  """
            CREATE TABLE storehouse (
                uid INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT DEFAULT '',
                plant TEXT DEFAULT ''
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
    async def executeDBCursor(cls, command: str) -> Optional[List[Any]]:
        """执行自定义SQL并返回查询结果

        Args:
            command (str): SQL查询语句

        Returns:
            Optional[List[Any]]: 查询结果列表（成功时），None（失败时）
        """
        if  len(command) <= 0:
            logger.warning("空数据库命令")
            return None

        try:
            async with cls.m_pDB.execute(command) as cursor:
                # 将Row对象转换为字典列表
                results = [dict(row) for row in await cursor.fetchall()]
                return results
        except Exception as e:
            logger.error(f"数据库执行失败: {e}")
            return None

    @classmethod
    async def initUserInfoByUid(cls,
                                uid: str, name: str = "", exp: int = 0, point: int = 100):
        #用户信息
        userInfo =  f"""
            INSERT INTO user (uid, name, exp, point) VALUES ({uid}, '{name}', {str(exp)}, {str(point)})
            """

        #用户仓库
        userStorehouse = f"""
            INSERT INTO storehouse (uid) VALUES ({uid});
            """

        userSoilInfo = f"""
            INSERT INTO soil (uid) VALUES ({uid});
            """

        if not await cls.executeDB(userInfo):
            return False

        if not await cls.executeDB(userStorehouse):
            return False

        if not await cls.executeDB(userSoilInfo):
            return False

        return True

    @classmethod
    async def getUserInfoByUid(cls, uid: str) -> list[dict]:
        """根据用户Uid获取用户信息

        Args:
            uid (str): 用户Uid

        Returns:
            list[dict]: 用户信息
        """
        if len(uid) <= 0:
            return []

        try:
            async with cls.m_pDB.execute(
                "SELECT * FROM user WHERE uid = ?", (uid,)
            ) as cursor:
                results = []

                async for row in cursor:
                    user_dict = {
                        "uid": row[0],
                        "name": row[1],
                        "exp": row[2],
                        "point": row[3],
                    }
                    results.append(user_dict)

                return results
        except Exception as e:
            logger.warning(f"getUserInfoByUid查询失败: {e}")
            return []

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
            async with cls.m_pDB.execute(
                """UPDATE user
                SET point = ?
                WHERE uid = ?
                RETURNING point""",
                (point, uid)
            ) as cursor:
                async for row in cursor:
                    return int(row[0])

            logger.info(f"未找到用户或未修改数据: uid={uid}")
            return -1
        except Exception as e:
            # 记录详细错误日志（建议记录堆栈）
            logger.error(f"更新失败: {e}")
            return -1

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
            return -1

        level = await cls.getUserLevelByUid(uid)
        soilNumber = 0
        soil_list = g_pJsonManager.m_pLevel['soil'] # type: ignore

        #获取解锁地块
        for soil in soil_list:
            if level >= soil:
                soilNumber += 1

        return soilNumber

    @classmethod
    async def getUserSoilStatusBySoilID(cls, uid: str, soil: str) -> bool:
        """根据土地块获取用户土地状态

        Args:
            uid (str): 用户Uid
            soil (str): 土地块

        Returns:
            bool: 是否可以播种
        """
        if len(uid) <= 0:
            return False

        async with cls.m_pDB.execute(f"SELECT {soil} FROM soil WHERE uid = '{uid}'") as cursor:
            async for row in cursor:
                if row[0] == None:
                    return True

        return False

    @classmethod
    async def updateUserSoilStatusBySowing(cls, uid: str, soil: str, plant: str) -> bool:

        if len(uid) <= 0:
            return False

        #获取种子信息 这里能崩我吃
        plantInfo = g_pJsonManager.m_pPlant['plant'][plant] # type: ignore


        currentTime = datetime.now()
        newTime = currentTime + timedelta(minutes=int(plantInfo['time']))

        #种子名称，当前阶段，预计长大/预计下个阶段，地状态：0：无 1：长草 2：生虫 3：缺水 4：枯萎状态
        status = f"{plant},1,{int(newTime.timestamp())},0"

        sql = f"UPDATE soil SET {soil} = '{status}' WHERE uid = '{uid}'"

        return await cls.executeDB(sql)

    @classmethod
    async def getUserPlantByUid(cls, uid: str) -> str:
        """获取用户仓库种子信息

        Args:
            info (list[dict]): 用户信息

        Returns:
            str: 仓库种子信息
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
        """添加用户仓库种子信息

        Args:
            info (list[dict]): 种子信息

        Returns:
            bool: 是否添加成功
        """

        if len(uid) <= 0:
            return False

        sql = f"UPDATE storehouse SET plant = '{plant}' WHERE uid = '{uid}'"

        return await cls.executeDB(sql)

g_pSqlManager = CSqlManager()
