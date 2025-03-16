import os
import aiosqlite
import asyncio

from zhenxun.services.log import logger
from zhenxun.configs.path_config import DATA_PATH, IMAGE_PATH, TEMPLATE_PATH

from .config import (
    g_sDBPath,
    g_sDBFilePath
)

class CSqlManager:
    def __init__(self):
        g_sDBPath.mkdir(parents=True, exist_ok=True)

    def __del__(self):
        if self.m_pDB:
            self.m_pDB.close()
            self.m_pDB = None

    @classmethod
    async def init(cls) -> bool:
        bIsExist = os.path.exists(g_sDBFilePath)

        cls.m_pDB = await aiosqlite.connect(g_sDBFilePath)

        if bIsExist == False:
            #TODO 缺少判断创建失败事件
            await cls.createDB()

        return True

    @classmethod
    async def createDB(cls) -> bool:
        """初始化数据库表

        Returns:
            bool: 是否创建成功
        """

        try:
            await cls.m_pDB.execute('''
                CREATE TABLE user (
                    uid INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    level INTEGER DEFAULT 1,
                    point INTEGER DEFAULT 0
                );
            ''')
            await cls.m_pDB.commit()
            return True
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    @classmethod
    async def getUserByUid(cls, uid : str) -> list[dict]:
        """根据用户Uid获取用户信息

        Args:
            uid (str): 用户Uid

        Returns:
            list[dict]: 用户信息
        """
        if len(uid) <= 0:
            return []

        try:
            async with cls.m_pDB.execute("SELECT * FROM user WHERE uid = ?", (uid,)) as cursor:
                results = []

                async for row in cursor:
                    user_dict = {
                        'uid': row[0],
                        'name': row[1],
                        'level': row[2],
                        'point': row[3]
                    }
                    results.append(user_dict)

                return results
        except Exception as e:
            logger.warning(f"查询失败: {e}")
            return []

    @classmethod
    async def appendUserByUserInfo(cls, info : list[dict]) -> bool:
        """添加用户信息

        Args:
            info (list[dict]): 用户信息

        Returns:
            bool: 是否添加成功
        """

        try:
            await cls.m_pDB.execute('''
                INSERT INTO user (uid, name, level, point) VALUES (?, ?, ?, ?)
            ''', (info['uid'], info['name'], info['level'], info['point']))
            await cls.m_pDB.commit()

            return True
        except Exception as e:
            logger.warning(f"添加失败: {e}")
            return False