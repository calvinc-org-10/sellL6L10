from typing import (Any, Dict, List, Optional, )

from sqlalchemy import Row, RowMapping, Select, Table, select, text

from .menucommand_constants import (MENUCOMMANDS, COMMANDNUMBER, )
from .database import cMenu_Session

from .utils import (retListofQSQLRecord, recordsetList, select_with_join_excluding, )

# self, menuID: str, menuName: str, menuItems:Dict[int,Dict]):
# {'keys': {'MenuGroup': 1, 'MenuID': 0, 'OptionNumber': 0}, 
#     'values': {etc}}
initmenu_menulist = [
{'MenuID': -1, 'OptionNumber': 0,
    'OptionText': 'New Menu', 'Command': None, 'Argument': 'Default', 'PWord': '', 'TopLine': 1, 'BottomLine': 1, },
{'MenuID': -1, 'OptionNumber': 11,
    'OptionText': 'Edit Menu', 'Command': COMMANDNUMBER.EditMenu, 'Argument': '', 'PWord': '', },
{'MenuID': -1, 'OptionNumber': 19,
    'OptionText': 'Change Password', 'Command': COMMANDNUMBER.ChangePW, 'Argument': '', 'PWord': '', },
{'MenuID': -1, 'OptionNumber': 20,
    'OptionText': 'Go Away!', 'Command': COMMANDNUMBER.ExitApplication, 'Argument': '', 'PWord': '', },
]

newgroupnewmenu_menulist = [
{'MenuID': 0, 'OptionNumber': 0,
    'OptionText': 'New Menu', 'Command': None, 'Argument': 'Default', 'PWord': '', 'TopLine': 1, 'BottomLine': 1, },
{'MenuID': 0, 'OptionNumber': 19,
    'OptionText': 'Change Password', 'Command': COMMANDNUMBER.ChangePW, 'Argument': '', 'PWord': '', },
{'MenuID': 0, 'OptionNumber': 20,
    'OptionText': 'Go Away!', 'Command': COMMANDNUMBER.ExitApplication, 'Argument': '', 'PWord': '', },
]

newmenu_menulist = [
{'OptionNumber': 0,
    'OptionText': 'New Menu', 'Command': None, 'Argument': '', 'PWord': '', 'TopLine': 1, 'BottomLine': 1, },
{'OptionNumber': 20,
    'OptionText': 'Return to Main Menu', 'Command': COMMANDNUMBER.LoadMenu, 'Argument': '0', 'PWord': '', },
]


from .models import menuGroups, menuItems

class MenuRecords:
    """A class for managing menu items in the database."""
    
    _tbl = menuItems
    _tblGroup = menuGroups

    def __init__(self):
        self.session = None

    def __enter__(self):
        self.session = cMenu_Session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            if exc_type is None:
                self.session.commit()
            else:
                self.session.rollback()
            self.session.close()

    def create(self, persist:bool = True, **kwargs) -> menuItems:
        """Create a new menu item record."""
        new_item = self._tbl(**kwargs)
        if persist:
            with cMenu_Session() as session:
                session.add(new_item)
                session.commit()
        #endif
        return new_item
    
    def get(self, record_id: int) -> Optional[menuItems]:
        """Get a menu item by its primary key."""
        with cMenu_Session() as session:
            return session.get(self._tbl, record_id)
    
    def update(self, record_id: int, **kwargs) -> Optional[menuItems]:
        """Update an existing menu item record."""
        with cMenu_Session() as session:
            item = session.get(self._tbl, record_id)
            if item:
                for key, value in kwargs.items():
                    setattr(item, key, value)
                session.commit()
                return item
        return None
    
    def delete(self, record_id: int) -> bool:
        """Delete a menu item record."""
        with cMenu_Session() as session:
            item = session.get(self._tbl, record_id)
            if item:
                session.delete(item)
                session.commit()
                return True
        return False
    
    def menuAttr(self, mGroup: int, mID: int, Opt: int, AttrName: str) -> Any:
        """Get a specific attribute from a menu item."""
        stmt = select(getattr(self._tbl, AttrName)).where(
            self._tbl.MenuGroup_id == mGroup,
            self._tbl.MenuID == mID,
            self._tbl.OptionNumber == Opt
        )
        with cMenu_Session() as session:
            return session.scalar(stmt)
    
    def minMenuID_forGroup(self, mGroup: int) -> Optional[int]:
        """
        Returns the minimum MenuID for the given MenuGroup.
        """
        stmt = select(self._tbl.MenuID).where(
            self._tbl.MenuGroup_id == mGroup,
            self._tbl.OptionNumber == 0
        ).order_by(self._tbl.MenuID.asc())
        with cMenu_Session() as session:
            retval = session.scalars(stmt).first()
        return retval

    def dfltMenuID_forGroup(self, mGroup:int) -> Optional[int]:
        stmt = select(self._tbl.MenuID).where(
            self._tbl.MenuGroup_id == mGroup,
            self._tbl.Argument.ilike('default'),
            self._tbl.OptionNumber == 0
            )
        with cMenu_Session() as session:
            retval = session.scalar(stmt)
        if not retval:
            # If no record found, we need to find the minimum MenuID for this group
            retval = self.minMenuID_forGroup(mGroup)
        return retval

    def dfltMenuGroup(self) -> Optional[int]:
        """
        Returns the minimum MenuGroup.
        """
        stmt = select(self._tbl.MenuGroup_id).order_by(self._tbl.MenuGroup_id.asc())
        with cMenu_Session() as session:
            retval = session.scalars(stmt).first()
        return retval
    
    def menuDict(self, mGroup:int, mID:int) ->  Dict[int,Dict[str, Any]]:
        # use selectjoin
        stmt = (
            select(*self._tbl.__table__.columns)
            .join(self._tblGroup, self._tbl.MenuGroup_id == self._tblGroup.id)
            .where(
                self._tbl.MenuGroup_id == mGroup,
                self._tbl.MenuID == mID
                )
            )
        with cMenu_Session() as session:
            result = session.execute(stmt).mappings()
            # Convert the result to a dictionary with OptionNumber as keys
            # and dictionaries of field values as values
            # Note: 'rec' is a RowMapping, so we can access fields by name
            retDict = { row['OptionNumber']: dict(row) for row in result }
        return retDict

    # def menuDBRecs(self, mGroup:int, mID:int) ->  QuerySet:
    def menuDBRecs(self, mGroup:int, mID:int) ->  Dict[int, menuItems]:
        # use selectjoin
        stmt = (
            select(self._tbl)
            .join(self._tblGroup, self._tbl.MenuGroup_id == self._tblGroup.id)
            .where(
                self._tbl.MenuGroup_id == mGroup,
                self._tbl.MenuID == mID
            )
        )
        with cMenu_Session() as session:
            result = session.execute(stmt).scalars()
            # Convert the result to a dictionary with OptionNumber as keys
            # and the menuItems objects as values
            retDict = { rec.OptionNumber: rec for rec in result }
        return retDict

    def menuExist(self, mGroup:int, mID:int) ->  bool:
        stmt = select(self._tbl).where(
            self._tbl.MenuGroup_id == mGroup,
            self._tbl.MenuID == mID,
            self._tbl.OptionNumber == 0
        )
        with cMenu_Session() as session:
            result = session.execute(stmt).first()
        # If the result is None, the menu does not exist
        # If the result is a Row or RowMapping, the menu exists
        return (result is not None)

    # TODO: generalize this, mebbe to a new class
    def recordsetList(self, retFlds:int|List[str] = retListofQSQLRecord, filter:Optional[str] = None) -> List:
        stmt:Select = select_with_join_excluding(self._tbl.__table__, self._tblGroup.__table__, (self._tbl.MenuGroup_id == self._tblGroup.id), ['id'])
        if retFlds == '*' or (isinstance(retFlds,List) and retFlds[0]=='*') or retFlds == retListofQSQLRecord:
            stmt = stmt
        elif isinstance(retFlds, List):
            # Filter the existing selected columns by name
            filtered_cols = [
                col for col in stmt.selected_columns
                if col.name in retFlds
            ]

            # Apply with_only_columns
            stmt = stmt.with_only_columns(*filtered_cols)
        else:
            stmt = stmt
        #endif retFlds
        if filter:
            stmt = stmt.where(text(filter))
        #endif filter

        with cMenu_Session() as session:
            records = session.execute(stmt)
            retList = list(records.mappings())

        return retList

    #enddef recordsetList

    def newgroupnewmenuDict(self, mGroup:int, mID:int) ->  List[Dict]:
        return newgroupnewmenu_menulist
    def newmenuDict(self, mGroup:int, mID:int) ->  List[Dict]:
        return newmenu_menulist
    