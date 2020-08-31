from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, Integer, String

Base = declarative_base()


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    # line_map = ...
    # functions = ...
    # globals = ...


class Function(Base):
    __tablename__ = "functions"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    start_line = Column(Integer)
    start_column = Column(Integer)

    # var_decls = ...
    # calls = ...
    # statements = ...


class Global(Base):
    __tablename__ = "globals"


class VarDecl(Base):
    __tablename__ = "var_decls"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type_ = Column(String)
    start_line = Column(Integer)
    start_column = Column(Integer)
    end_line = Column(Integer)
    end_column = Column(Integer)
    is_array = Column(Boolean)
    size = Column(Integer)


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True)
    expr = Column(String)
    name = Column(String)

    # arguments = ...


class Argument(Base):
    __tablename__ = "call_arguments"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    type_ = Column(String)


class Statement(Base):
    __tablename__ = "statements"

    start_line = Column(Integer)
    start_column = Column(Integer)
    end_line = Column(Integer)
    end_column = Column(Integer)
    expr = Column(String)
