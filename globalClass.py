from .config import CJsonManager
from .database import CSqlManager
from .drawImage import CDrawImageManager

g_pJsonManager = CJsonManager()

g_pSqlManager = CSqlManager()

g_pDrawImage = CDrawImageManager()
