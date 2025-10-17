# from PySide6.QtSql import (QSqlDatabase, QSqlQuery )

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

rootdir = "."
cMenu_dbName = f"{rootdir}\\cMenudb.sqlite"

# an Engine, which the Session will use for connection
# resources, typically in module scope
cMenu_engine = create_engine(
    f"sqlite:///{cMenu_dbName}",
    )
# a sessionmaker(), also in the same scope as the engine
cMenu_Session = sessionmaker(cMenu_engine)

def get_cMenu_session():
    return cMenu_Session()

##########################################################
###################    REPOSITORIES    ###################
##########################################################

from sqlalchemy import select
from typing import Generic, Sequence, TypeVar, Type

T = TypeVar("T")  # entity type

class Repository(Generic[T]):
    def __init__(self, session_factory, model: Type[T]):
        self._session_factory = session_factory
        self._model = model

    def get_all(
        self,
        whereclause=None,
        order_by=None
    ) -> list[T]:    # | list[tuple]:
        """
        Retrieve records with optional fields, filter, and ordering.

        :param fields: list/tuple of columns or ORM attributes (default: whole model)
            # fields is deprecated - get_all needs to always return an ORM instance - have the caller build a dict instead
        :param whereclause: SQLAlchemy expression for filtering
        :param order_by: column(s) or ORM attributes for ordering
        """

        # Build select
        stmt = select(self._model)

        if whereclause is not None:
            stmt = stmt.where(whereclause)

        if order_by is not None:
            if isinstance(order_by, (list, tuple)):
                stmt = stmt.order_by(*order_by)
            else:
                stmt = stmt.order_by(order_by)

        with self._session_factory() as session:
            rs = session.execute(stmt)

            # Full model objects
            results = rs.scalars().all()
            for row in results:
                session.expunge(row)

        return results
    
    def get_by_id(self, id_: int, newifnotfound: bool = False) -> T | None:
        with self._session_factory() as session:
            obj = session.get(self._model, id_)
            if obj:
                session.expunge(obj)
            elif newifnotfound:
                obj = self._model(id=id_) # type: ignore
            return obj

    def add(self, entity: T) -> T:
        with self._session_factory() as session:
            session.add(entity)
            session.commit()
            session.refresh(entity)
            session.expunge(entity)
        return entity

    def remove(self, entity: T) -> None:
        with self._session_factory() as session:
            obj = session.merge(entity)  # reattach if detached
            session.delete(obj)
            session.commit()

    def update(self, entity: T) -> T:
        with self._session_factory() as session:
            obj = session.merge(entity)  # reattach if detached
            session.commit()
            session.expunge(obj)
        return obj
