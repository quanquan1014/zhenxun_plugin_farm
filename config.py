import json
from pathlib import Path

from zhenxun.configs.path_config import DATA_PATH
from zhenxun.services.log import logger

g_sDBPath = DATA_PATH / "farm_db"
g_sDBFilePath = DATA_PATH / "farm_db/farm.db"

g_sResourcePath = Path(__file__).resolve().parent / "resource"


class CJsonManager:
    def __init__(self):
        self.m_pItem = None
        self.m_pPlant = None

    @classmethod
    async def init(cls) -> bool:
        if not await cls.initItem():
            return False

        if not await cls.initPlant():
            return False

        return True

    @classmethod
    async def initItem(cls) -> bool:
        current_file_path = Path(__file__)

        try:
            with open(
                current_file_path.resolve().parent / "config/item.json",
                encoding="utf-8",
            ) as file:
                cls.m_pItem = json.load(file)

                return True
        except FileNotFoundError:
            logger.warning("item.json 打开失败")
            return False
        except json.JSONDecodeError as e:
            logger.warning(f"item.json JSON格式错误: {e}")
            return False

    @classmethod
    async def initPlant(cls) -> bool:
        current_file_path = Path(__file__)

        try:
            with open(
                current_file_path.resolve().parent / "config/plant.json",
                encoding="utf-8",
            ) as file:
                cls.m_pPlant = json.load(file)

                return True
        except FileNotFoundError:
            logger.warning("plant.json 打开失败")
            return False
        except json.JSONDecodeError as e:
            logger.warning(f"plant.json JSON格式错误: {e}")
            return False
