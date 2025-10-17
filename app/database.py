from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# cMenu_dbName = "D:\\AppDev\\datasets\\hbl.sqlite"
# rootdir = "F:\\MXMLKMHS\\python\\MXMLKMHS-v0"
rootdir = "."
app_dbName = f"{rootdir}\\sellL6L10.sqlite"

# an Engine, which the Session will use for connection
# resources, typically in module scope
app_engine = create_engine(
    f"sqlite:///{app_dbName}",
    )
# a sessionmaker(), also in the same scope as the engine
app_Session = sessionmaker(app_engine)

def get_app_session():
    return app_Session()
