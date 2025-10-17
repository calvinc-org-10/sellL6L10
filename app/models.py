
from typing import Any
import decimal
from datetime import datetime, date

from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column, relationship, Session, )
from sqlalchemy import (Column, Date, Index, Integer, MetaData, String, Boolean, ForeignKey, SmallInteger, UniqueConstraint, inspect, )
from sqlalchemy.exc import IntegrityError

# from random import randint

from .database import app_Session

# standard sizes for decimal fields
HunThouMoney2Dec = {'max_digits':  8, 'decimal_places': 2}
HunThouMoney4Dec = {'max_digits': 10, 'decimal_places': 4}
HunMillMoney2Dec = {'max_digits': 11, 'decimal_places': 2}
HunMillMoney4Dec = {'max_digits': 13, 'decimal_places': 4}

# TODO: move to utils
def moneystr(value):
    return f"${value:,.2f}"
def str_to_dec(value):
    return decimal.Decimal(value.replace("$", "").replace(",", ""))

def datestrYMD(value):
    return value.strftime('%Y-%m-%d')
def strYMD_to_date(value):
    return datetime.strptime(value, '%Y-%m-%d').date()

ix_naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
ix_metadata_obj = MetaData(naming_convention=ix_naming_convention)

##########################################################
##########################################################
##########################################################

class L6L10sellBase(DeclarativeBase):
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

##########################################
##########################################

# TODO: rethink the lazy loads of relationships - cComboBoxFromDict and cDataList can do that work

class Parts(L6L10sellBase):
    __tablename__ = 'Parts'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    GPN: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    Description: Mapped[str] = mapped_column(String(250), default="", nullable=False)
    notes: Mapped[str] = mapped_column(String(250), default="", nullable=False)

    workorders_needing_part: Mapped[list["WorkOrderPartsNeeded"]] = relationship("WorkOrderPartsNeeded", 
        back_populates="part", cascade="all, delete-orphan"
        )
    tag_prefixes: Mapped[list["TagPrefixes"]] = relationship("TagPrefixes", 
        back_populates="part", cascade="all, delete-orphan",
        lazy="selectin" # use selectin loading for better performance when loading multiple parts with their tag prefixes
        )
    scans: Mapped[list["Scans"]] = relationship("Scans", 
        back_populates="part", cascade="all, delete-orphan", 
        lazy="selectin"
        )
    box_configurations: Mapped[list["BoxConfigurations"]] = relationship("BoxConfigurations", 
        back_populates="part", cascade="all, delete-orphan", 
        lazy="selectin"
        )

    def __repr__(self) -> str:
        return f"<menuGroups(id={self.id}, GPN='{self.GPN}')>"

    def __str__(self) -> str:
        return f"{self.GPN} ({self.Description})"
    

class Projects(L6L10sellBase):
    __tablename__ = 'Projects'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ProjectName: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    Color: Mapped[str] = mapped_column(String(15), nullable=False)
    
    workorders: Mapped[list["WorkOrders"]] = relationship("WorkOrders", 
        back_populates="project", cascade="all, delete-orphan",
        lazy="selectin" # use selectin loading for better performance when loading multiple projects with their workorders
        )
    
    __table_args__ = (
        UniqueConstraint('ProjectName'),
    )

    def __repr__(self) -> str:
        return f"<Projects(id={self.id}, ProjectName='{self.ProjectName}')>"

    def __str__(self) -> str:
        return f"{self.ProjectName} ({self.Color})"
    
    
class WorkOrders(L6L10sellBase):
    __tablename__ = 'WorkOrders'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    WOType: Mapped[str] = mapped_column(String(5), default='PK', nullable=False)
    CIMSNum: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    WOMAid: Mapped[str] = mapped_column(String(25), nullable=False)
    MRRequestor: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    Project_id: Mapped[int] = mapped_column(Integer, ForeignKey('Projects.id'), nullable=False)
    notes: Mapped[str] = mapped_column(String(250), default="", nullable=False)
    
    project: Mapped[Projects] = relationship("Projects", 
        back_populates="workorders",
        lazy="joined" # use joined loading for better performance when loading a workorder with its project
        )
    parts_needed: Mapped[list["WorkOrderPartsNeeded"]] = relationship("WorkOrderPartsNeeded", 
        back_populates="workorder", cascade="all, delete-orphan",
        lazy="selectin"
        )
    scans: Mapped[list["Scans"]] = relationship("Scans", 
        back_populates="workorder", cascade="all, delete-orphan",
        lazy="selectin"
        )

    __table_args__ = (
        UniqueConstraint('CIMSNum'),
        Index('ix_workorders_womaid', 'WOMAid'),        # regular index on WOMAid
    )

    def __repr__(self) -> str:
        return f"<WorkOrders(id={self.id}, CIMSNum='{self.WOType}{self.CIMSNum}')>"

    def __str__(self) -> str:
        return f"{self.WOType}{self.CIMSNum} ({self.WOMAid})"


class PickPriorities(L6L10sellBase):
    __tablename__ = 'PickPriorities'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    AbsolutePriority: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    PriorityWords: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str] = mapped_column(String(250), default="", nullable=False)

    __table_args__ = (
        UniqueConstraint('AbsolutePriority'),
    )
    
    def __repr__(self) -> str:
        return f"<PickPriorities(id={self.id}, AbsolutePriority={self.AbsolutePriority}, PriorityWords='{self.PriorityWords}')>"

    def __str__(self) -> str:
        return f"{self.AbsolutePriority} ({self.PriorityWords})"

class WorkOrderPartsNeeded(L6L10sellBase):
    # aka PickList
    __tablename__ = 'WorkOrderPartsNeeded'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    WorkOrders_id: Mapped[int] = mapped_column(Integer, ForeignKey('WorkOrders.id'), nullable=False)
    Parts_id: Mapped[int] = mapped_column(Integer, ForeignKey('Parts.id'), nullable=False)
    targetQty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(15), default="", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="", nullable=False)       # suggestions from PickPriorities
    notes: Mapped[str] = mapped_column(String(250), default="", nullable=False)

    workorder: Mapped[WorkOrders] = relationship("WorkOrders", 
        back_populates="parts_needed",
        lazy="joined" # use joined loading for better performance when loading a workorder part needed with its workorder
        )
    part: Mapped[Parts] = relationship("Parts", 
        back_populates="workorders_needing_part",
        lazy="joined" # use joined loading for better performance when loading a part with its workorder parts needed
        )

    __table_args__ = (
        UniqueConstraint('WorkOrders_id', 'Parts_id'),
    )

    def __repr__(self) -> str:
        return f"<WorkOrderPartsNeeded(id={self.id}, WorkOrders_id={self.WorkOrders_id}, Parts_id={self.Parts_id})>"

    def __str__(self) -> str:
        return f"WorkOrderPartsNeeded: {self.WorkOrders_id} - {self.Parts_id}"
    
    
class TagPrefixes(L6L10sellBase):
    __tablename__ = 'TagPrefixes'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    Parts_id: Mapped[int] = mapped_column(Integer, ForeignKey('Parts.id'), nullable=False)
    boxqty: Mapped[str] = mapped_column(String(30), default="", nullable=False)
    notes: Mapped[str] = mapped_column(String(250), default="", nullable=False)

    part: Mapped[Parts] = relationship("Parts", 
        back_populates="tag_prefixes",
        lazy="joined" # use joined loading for better performance when loading a tag prefix with its part
        )

    def __repr__(self) -> str:
        return f"<TagPrefixes(id={self.id}, Prefix='{self.Prefix}', Parts_id={self.Parts_id})>"
    
    def __str__(self) -> str:
        return f"{self.Prefix} ({self.Parts_id})"


class Scans(L6L10sellBase):
    __tablename__ = 'Scans'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pickDate: Mapped[date] = mapped_column(Date, nullable=False)
    wave: Mapped[int] = mapped_column(Integer, nullable=False)
    TagID: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    Parts_id: Mapped[int] = mapped_column(Integer, ForeignKey('Parts.id'), nullable=False)
    WO_id: Mapped[int] = mapped_column(Integer, ForeignKey('WorkOrders.id'), nullable=False)
    qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    splitQtyToLeave: Mapped[int] = mapped_column(Integer, nullable=True)
    palletMark: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    staged_at: Mapped[str] = mapped_column(String(30), default="", nullable=False)
    notes: Mapped[str] = mapped_column(String(250), default="", nullable=False)

    part: Mapped[Parts] = relationship("Parts", 
        back_populates="scans",
        lazy="joined"
        )
    workorder: Mapped[WorkOrders] = relationship("WorkOrders", 
        back_populates="scans",
        lazy="joined"
        )

    __table_args__ = (
        UniqueConstraint('TagID'),
    )

    def __repr__(self) -> str:
        return f"<Scans(id={self.id}, TagID='{self.TagID}', Parts_id={self.Parts_id}, WO_id={self.WO_id})>"

    def __str__(self) -> str:
        return f"Scans: {self.TagID} - {self.Parts_id} - {self.WO_id}"
    
class BoxConfigurations(L6L10sellBase):
    __tablename__ = 'BoxConfigurations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Parts_id: Mapped[int] = mapped_column(Integer, ForeignKey('Parts.id'), nullable=False)
    palletqty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    boxqty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unitqty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    notes: Mapped[str] = mapped_column(String(250), default="", nullable=False)

    part: Mapped[Parts] = relationship("Parts", 
        back_populates="box_configurations",
        lazy="joined"
        )

    __table_args__ = (
        UniqueConstraint('Parts_id', 'palletqty', 'boxqty', 'unitqty'),
    )
    
    def __repr__(self) -> str:
        return f"<BoxConfigurations(id={self.id}, Parts_id={self.Parts_id}, palletqty={self.palletqty}, boxqty={self.boxqty}, unitqty={self.unitqty})>"

    def __str__(self) -> str:
        return f"BoxConfigurations: {self.Parts_id} - {self.palletqty} - {self.boxqty} - {self.unitqty}"
    

##########################################################
##########################################################

from cMenu.database import Repository
# Create a repository for each model
class L6L10sellRepositories():
    Parts = Repository(app_Session, Parts)
    Projects = Repository(app_Session, Projects)
    WorkOrders = Repository(app_Session, WorkOrders)
    PickPriorities = Repository(app_Session, PickPriorities)
    WorkOrderPartsNeeded = Repository(app_Session, WorkOrderPartsNeeded)
    TagPrefixes = Repository(app_Session, TagPrefixes)
    Scans = Repository(app_Session, Scans)
    BoxConfigurations = Repository(app_Session, BoxConfigurations)

##########################################################
##########################################################

L6L10sellBase.metadata.create_all(app_Session().get_bind())
# Ensure that the tables are created when the module is imported
# Parts()
# Projects()
# WorkOrders()
# PickPriorities()
# WorkOrderPartsNeeded()
# TagPrefixes()
# Scans()
# BoxConfigurations()
