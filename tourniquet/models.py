from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    functions = relationship("Function")
    global_variables = relationship("Global")


class Function(Base):
    __tablename__ = "functions"

    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey("modules.id"))
    module = relationship("Module", back_populates="functions")

    name = Column(String)
    start_line = Column(Integer)
    start_column = Column(Integer)

    var_decls = relationship("VarDecl")
    calls = relationship("Call")
    statements = relationship("Statement")


class Global(Base):
    __tablename__ = "globals"

    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey("modules.id"))
    module = relationship("Module", back_populates="functions")

    name = Column(String)
    type_ = Column(String)
    start_line = Column(Integer)
    start_column = Column(Integer)
    end_line = Column(Integer)
    end_column = Column(Integer)
    is_array = Column(Boolean)
    size = Column(Integer)


class VarDecl(Base):
    __tablename__ = "var_decls"

    id = Column(Integer, primary_key=True)
    function_id = Column(Integer, ForeignKey("functions.id"))
    function = relationship("Function", back_populates="var_decls")

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
    function_id = Column(Integer, ForeignKey("functions.id"))
    function = relationship("Function", back_populates="calls")

    expr = Column(String)
    name = Column(String)

    arguments = relationship("Argument")


class Argument(Base):
    __tablename__ = "call_arguments"

    id = Column(Integer, primary_key=True)
    call_id = Column(Integer, ForeignKey("calls.id"))
    call = relationship("Call", back_populates="arguments")

    name = Column(String)
    type_ = Column(String)


class Statement(Base):
    __tablename__ = "statements"

    id = Column(Integer, primary_key=True)
    function_id = Column(Integer, ForeignKey("functions.id"))
    function = relationship("Function", back_populates="statements")

    start_line = Column(Integer)
    start_column = Column(Integer)
    end_line = Column(Integer)
    end_column = Column(Integer)
    expr = Column(String)
