import os

import aiosqlite

from zhenxun.services.log import logger

from .config import CJsonManager, g_sDBFilePath, g_sDBPath


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
        """初始化数据库表

        Returns:
            bool: 是否创建成功
        """

        try:
            await cls.m_pDB.execute("""
                CREATE TABLE user (
                    uid INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    exp INTEGER DEFAULT 0,
                    point INTEGER DEFAULT 0
                );
            """)
            await cls.m_pDB.commit()
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

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
            logger.warning(f"查询失败: {e}")
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
                "SELECT point FROM user WHERE uid = ?", (uid,)
            ) as cursor:
                async for row in cursor:
                    return int(row[0])
        except Exception as e:
            logger.warning(f"查询失败: {e}")
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
            async with cls.m_pDB.execute(
                "SELECT exp FROM user WHERE uid = ?", (uid,)
            ) as cursor:
                async for row in cursor:
                    exp = int(row[0])

                    #获取等级列表
                    levelDict = g_pJsonManager.m_pLevel['level']

                    sorted_keys = sorted(levelDict.keys(), key=lambda x: int(x), reverse=True)
                    for key in sorted_keys:
                        if exp >= levelDict[key]:
                            return int(key)
        except Exception as e:
            logger.warning(f"查询失败: {e}")
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
    async def appendUserByUserInfo(cls, info: list[dict]) -> bool:
        """添加用户信息

        Args:
            info (list[dict]): 用户信息

        Returns:
            bool: 是否添加成功
        """

        try:
            await cls.m_pDB.execute(
                """
                INSERT INTO user (uid, name, exp, point) VALUES (?, ?, ?, ?)
            """,
                (info["uid"], info["name"], info["exp"], info["point"]),
            )
            await cls.m_pDB.commit()

            return True
        except Exception as e:
            logger.warning(f"添加失败: {e}")
            return False

g_pSqlManager = CSqlManager()
