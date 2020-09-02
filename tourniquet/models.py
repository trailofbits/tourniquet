from threading import local

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()
Base.local = local()


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    functions = relationship("Function")
    global_variables = relationship("Global")

    def __repr__(self):
        return f"<Module {self.name}>"


class Function(Base):
    __tablename__ = "functions"

    id = Column(Integer, primary_key=True)
    module_name = Column(Integer, ForeignKey("modules.name"))
    module = relationship("Module", back_populates="functions")

    name = Column(String)
    start_line = Column(Integer)
    start_column = Column(Integer)
    end_line = Column(Integer)
    end_column = Column(Integer)

    var_decls = relationship("VarDecl")
    calls = relationship("Call")
    statements = relationship("Statement")

    def __repr__(self):
        return f"<Function {self.name}>"


class Global(Base):
    __tablename__ = "globals"

    id = Column(Integer, primary_key=True)
    module_name = Column(Integer, ForeignKey("modules.name"))
    module = relationship("Module", back_populates="global_variables")

    name = Column(String)
    type_ = Column(String)
    start_line = Column(Integer)
    start_column = Column(Integer)
    end_line = Column(Integer)
    end_column = Column(Integer)
    is_array = Column(Boolean)
    size = Column(Integer)

    def __repr__(self):
        return f"<Global {self.name}>"


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

    def __repr__(self):
        return f"<VarDecl {self.type_} {self.name}>"


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True)
    function_id = Column(Integer, ForeignKey("functions.id"))
    function = relationship("Function", back_populates="calls")

    expr = Column(String)
    name = Column(String)
    start_line = Column(Integer)
    start_column = Column(Integer)
    end_line = Column(Integer)
    end_column = Column(Integer)

    arguments = relationship("Argument")

    def __repr__(self):
        return f"<Call {self.expr}>"


class Argument(Base):
    __tablename__ = "call_arguments"

    id = Column(Integer, primary_key=True)
    call_id = Column(Integer, ForeignKey("calls.id"))
    call = relationship("Call", back_populates="arguments")

    name = Column(String)
    type_ = Column(String)

    def __repr__(self):
        return f"<Argument {self.type_} {self.name}>"


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

    def __repr__(self):
        return f"<Statement {self.expr}>"


class DB:
    @classmethod
    def create(cls, db_path, echo=False):
        engine = create_engine(f"sqlite:///{db_path}", echo=echo)

        session = sessionmaker(bind=engine)()
        Base.local.bind = engine
        Base.metadata.create_all(engine)

        return cls(session, db_path)

    def __init__(self, session, db_path):
        self.session = session
        self.db_path = db_path

    def query(self, *args, **kwargs):
        return self.session.query(*args, **kwargs)
