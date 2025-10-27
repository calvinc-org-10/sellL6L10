# from functools import partial
from typing import (Callable, List, )

from PySide6.QtCore import (
    QModelIndex,
    )
from PySide6.QtGui import (
    QIcon,
    )
from sqlalchemy.orm import (
    sessionmaker, Session,
    )

from cMenu.utils import (
    cSimpRecSbFmRecord,
    cQFmFldWidg,
    cDataList,
    get_primary_key_column, 
    )
from cMenu.menucommand_constants import MENUCOMMANDS


Nochoice = {'---': None}    # only needed for combo boxes, not datalists
_NUM_menuBUTTONS = 20


