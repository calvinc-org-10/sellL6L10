
from typing import Any
from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column, relationship, Session, )
from sqlalchemy import (Column, Integer, MetaData, String, Boolean, ForeignKey, SmallInteger, UniqueConstraint, inspect, )
from sqlalchemy.exc import IntegrityError

from random import randint

from PySide6.QtCore import (QObject, )
from PySide6.QtWidgets import (QApplication, )
from .utils import (pleaseWriteMe, )

from .database import cMenu_Session
from .menucommand_constants import MENUCOMMANDS, COMMANDNUMBER
from .dbmenulist import (newgroupnewmenu_menulist, )


tblName_menuGroups = 'cMenu_menuGroups'
tblName_menuItems = 'cMenu_menuItems'
tblName_cParameters = 'cMenu_cParameters'
tblName_cGreetings = 'cMenu_cGreetings'


ix_naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
ix_metadata_obj = MetaData(naming_convention=ix_naming_convention)

class cMenuBase(DeclarativeBase):
    __abstract__ = True
    metadata = ix_metadata_obj
    # This class is used to define the base for SQLAlchemy models, if needed.
    # It can be extended with common methods or properties for all models.
    
    def setValue(self, field: str, value: Any):
        """
        Set a value for a field in the model instance.
        :param field: The name of the field to set.
        :param value: The value to set for the field.
        """
        setattr(self, field, value)
    
    def getValue(self, field: str) -> Any:
        """
        Get the value of a field in the model instance.
        :param field: The name of the field to get.
        :return: The value of the field.
        """
        return getattr(self, field, None)

    # these look good on paper, but I need the caller to have control over the Session. Best to let caller do all the heavy lifting
    # def save(self, session: Session = cMenu_Session()):
    #     """
    #     Save the current instance to the database.
    #     :param session: Optional SQLAlchemy session to use for saving.
    #     If not provided, a new session will be created.
    #     """
    #     if session is None:
    #         session = cMenu_Session()
    #     try:
    #         session.add(self)
    #         session.commit()
    #     except IntegrityError:
    #         session.rollback()
    #         raise
    #     finally:
    #         session.close()
    
    # def delete(self, session: Session = cMenu_Session()) -> Any:
    #     """
    #     Delete the current instance from the database.
    #     :param session: Optional SQLAlchemy session to use for deletion.
    #     If not provided, a new session will be created.
    #     """
    #     if session is None:
    #         session = cMenu_Session()
    #     try:
    #         session.delete(self)
    #         session.commit()
    #         retval = True
    #     except IntegrityError as e:
    #         session.rollback()
    #         retval = e
    #     except Exception as e:
    #         session.rollback()
    #         retval = e
    #     finally:
    #         session.close()

    #     return retval

class menuGroups(cMenuBase):
    """
    id = models.AutoField(primary_key=True)
    GroupName = models.CharField(max_length=100, unique=True)
    GroupInfo = models.CharField(max_length=250, default="")
    """
    
    __tablename__ = tblName_menuGroups

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    GroupName: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    GroupInfo: Mapped[str] = mapped_column(String(250), default="", nullable=False)

    def __repr__(self) -> str:
        return f"<menuGroups(id={self.id}, GroupName='{self.GroupName}')>"

    def __str__(self) -> str:
        return f"{self.GroupName} ({self.GroupInfo})"

    @classmethod
    def _createtable(cls, engine):
        # Create tables if they don't exist
        cMenuBase.metadata.create_all(engine)

        session = Session(engine)
        try:
            # Check if any group exists
            if not session.query(cls).first():
                # Add starter group
                starter = cls(GroupName="Group Name", GroupInfo="Group Info")
                session.add(starter)
                session.commit()
                # Add default menu items for the starter group
                starter_id = starter.id
                menu_items = [
                    menuItems(
                        MenuGroup_id=starter_id, MenuID=0, OptionNumber=0, 
                        OptionText='New Menu', 
                        Command=None, Argument='Default', 
                        PWord='', TopLine=True, BottomLine=True
                        ),
                    menuItems(
                        MenuGroup_id=starter_id, MenuID=0, OptionNumber=11, 
                        OptionText='Edit Menu', 
                        Command=COMMANDNUMBER.EditMenu, Argument='', 
                        PWord='', TopLine=None, BottomLine=None
                        ),
                    menuItems(
                        MenuGroup_id=starter_id, MenuID=0, OptionNumber=19, 
                        OptionText='Change Password', 
                        Command=COMMANDNUMBER.ChangePW, Argument='', 
                        PWord='', TopLine=None, BottomLine=None
                        ),
                    menuItems(
                        MenuGroup_id=starter_id, MenuID=0, OptionNumber=20, 
                        OptionText='Go Away!', 
                        Command=COMMANDNUMBER.ExitApplication, Argument='', 
                        PWord='', TopLine=None, BottomLine=None
                        ),
                    ]
                session.add_all(menu_items)
                session.commit()
        except IntegrityError:
            session.rollback()
        finally:
            session.close()

        
class menuItems(cMenuBase):
    __tablename__ = tblName_menuItems
    _rltblFld = 'MenuGroup_id'
    _rltblName = tblName_menuGroups

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    MenuGroup_id: Mapped[int] = mapped_column(Integer, ForeignKey(f"{_rltblName}.id"))
    MenuID: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    OptionNumber: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    OptionText: Mapped[str] = mapped_column(String(250), nullable=False, default="")
    Command: Mapped[int] = mapped_column(Integer, nullable=True)
    Argument: Mapped[str] = mapped_column(String(250), nullable=False, default="")
    PWord: Mapped[str] = mapped_column(String(250), nullable=False, default="")
    TopLine: Mapped[bool] = mapped_column(nullable=True)
    BottomLine: Mapped[bool] = mapped_column(nullable=True)

    __table_args__ = (
        UniqueConstraint('MenuGroup_id', 'MenuID', 'OptionNumber'),     # Unique constraint for MenuGroup_id, MenuID, and OptionNumber
        {'sqlite_autoincrement': True, # Enable autoincrement for the primary key
         'extend_existing': True},
    )
    
    def __repr__(self) -> str:
        return f"<menuItems(id={self.id}, MenuID={self.MenuID}, OptionNumber={self.OptionNumber}, OptionText='{self.OptionText}')>"

    def __str__(self) -> str:
        return f"{self.OptionText} (ID: {self.MenuID}, Option: {self.OptionNumber})"

    def __init__(self, **kw: Any):
        """
        Initialize a new menuItems instance. If the menu table doesn't exist, it will be created.
        If the menuGroups table doesn't exist, it will also be created, and a starter group and menu will be added.
        :param kw: Keyword arguments for the menuItems instance.
        """
        inspector = inspect(cMenu_Session().get_bind())
        if not inspector.has_table(self.__tablename__):
            # If the table does not exist, create it
            cMenuBase.metadata.create_all(cMenu_Session().get_bind())
            # Optionally, you can also create a starter group and menu here
            menuGroups._createtable(cMenu_Session().get_bind())
        #endif not inspector.has_table():
        super().__init__(**kw)

    # @classmethod
    # def _createtable(cls, engine):
    #     cMenuBase.metadata.create_all(engine)


class cParameters(cMenuBase):
    __tablename__ = tblName_cParameters

    ParmName: Mapped[str] = mapped_column(String(100), primary_key=True)
    ParmValue: Mapped[str] = mapped_column(String(512), nullable=False)
    UserModifiable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    Comments: Mapped[str] = mapped_column(String(512), nullable=False)

    def __repr__(self) -> str:
        return f"<cParameters(ParmName='{self.ParmName}')>"

    def __str__(self) -> str:
        return f"{self.ParmName} ({self.ParmValue})"

    # @classmethod
    # def _createtable(cls, engine):
    #     # Create tables if they don't exist
    #     cMenuBase.metadata.create_all(engine, cls.)

# def getcParm(req, parmname):
# use code like below instead
    # """
    # Get the value of a parameter from the cParameters table.
    # :param req: The request object (not used in this function).
    # :param parmname: The name of the parameter to retrieve.
    # :return: The value of the parameter or an empty string if not found.
    # """
    # session = cMenu_Session()
    # try:
    #     param = session.query(cParameters).filter_by(ParmName=parmname).first()
    #     return param.ParmValue if param else ''
    # finally:
    #     session.close()

# def setcParm(req, parmname, parmvalue):
    # """Set the value of a parameter in the cParameters table.
    # :param req: The request object (not used in this function).
    # :param parmname: The name of the parameter to set.
    # :param parmvalue: The value of the parameter to set.
    # """


class cGreetings(cMenuBase):
    """
    id = models.AutoField(primary_key=True)
    Greeting = models.CharField(max_length=2000)
    """
    __tablename__ = tblName_cGreetings

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Greeting: Mapped[str] = mapped_column(String(2000), nullable=False)
    __table_args__ = (
        {'sqlite_autoincrement': True,
         'extend_existing': True},
    )
    
    def __repr__(self) -> str:
        return f"<cGreetings(id='{self.id}', Greeting='{self.Greeting}')>"

    def __str__(self) -> str:
        return f"{self.Greeting} (ID: {self.id})"


cMenuBase.metadata.create_all(cMenu_Session().get_bind())
# Ensure that the tables are created when the module is imported
menuGroups._createtable(cMenu_Session().get_bind())
menuItems() #._createtable(cMenu_Session().get_bind())
cParameters() #._createtable(cMenu_Session().get_bind())
cGreetings() #._createtable(cMenu_Session().get_bind())