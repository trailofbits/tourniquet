from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class Module(Base):
    """
    Represents a C or C++ file, or "module" in Clang's terminology.
    """

    __tablename__ = "modules"

    id = Column(Integer, primary_key=True)
    """
    This module's database ID.
    """

    name = Column(String, unique=True)
    """
    The name (i.e. source file) of this module.
    """

    functions = relationship("Function")
    """
    The `Function`s present in this module.
    """

    global_variables = relationship("Global")
    """
    The `Global`s present in this module.
    """

    statements = relationship("Statement")
    """
    The `Statement`s present in this module.
    """

    # TODO(ww): Module -> [VarDecl], -> [Call] relationships

    def __repr__(self):
        return f"<Module {self.name}>"


class Function(Base):
    """
    Represents a single C or C++ function.
    """

    __tablename__ = "functions"

    id = Column(Integer, primary_key=True)
    """
    This function's database ID.
    """

    module_name = Column(Integer, ForeignKey("modules.name"))
    """
    The name of the `Module` that this function belongs to.
    """

    module = relationship("Module", back_populates="functions")
    """
    The `Module` that this function belongs to.
    """

    name = Column(String)
    """
    The name of this function.
    """

    start_line = Column(Integer)
    """
    The line that this function begins on.
    """

    start_column = Column(Integer)
    """
    The column that this function begins on.
    """

    end_line = Column(Integer)
    """
    The line that this function ends on.
    """

    end_column = Column(Integer)
    """
    The column that this function ends on.
    """

    var_decls = relationship("VarDecl")
    """
    The `VarDecl`s present in this function.
    """

    calls = relationship("Call")
    """
    The `Call`s present in this function.
    """

    statements = relationship("Statement")
    """
    The `Statement`s present in this function.
    """

    def __repr__(self):
        return f"<Function {self.name}>"


class Global(Base):
    """
    Represents a global variable declaration.
    """

    __tablename__ = "globals"

    id = Column(Integer, primary_key=True)
    """
    This global's database ID.
    """

    module_name = Column(Integer, ForeignKey("modules.name"))
    """
    The name of the `Module` that this global belongs to.
    """

    module = relationship("Module", back_populates="global_variables")
    """
    The `Module` that this global belongs to.
    """

    name = Column(String)
    """
    The declared name of this global.
    """

    type_ = Column(String)
    """
    The declared type of this global.
    """

    start_line = Column(Integer)
    """
    The line that this global begins on.
    """

    start_column = Column(Integer)
    """
    The column that this global begins on.
    """

    end_line = Column(Integer)
    """
    The line that this global ends on.
    """

    end_column = Column(Integer)
    """
    The column that this global ends on.
    """

    is_array = Column(Boolean)
    """
    Whether or not this global's declaration is for an array type.
    """

    size = Column(Integer)
    """
    The size of this global, in bytes.
    """

    def __repr__(self):
        return f"<Global {self.name}>"


class VarDecl(Base):
    """
    Represents a local variable or function parameter declaration.
    """

    __tablename__ = "var_decls"

    id = Column(Integer, primary_key=True)
    """
    This declaration's database ID.
    """

    function_id = Column(Integer, ForeignKey("functions.id"))
    """
    The ID of the `Function` that this declaration is present in.
    """

    function = relationship("Function", back_populates="var_decls")
    """
    The `Function` that this declaration is present in.
    """

    name = Column(String)
    """
    The name of this declared variable.
    """

    type_ = Column(String)
    """
    The type of this declared variable.
    """

    start_line = Column(Integer)
    """
    The line that this declaration begins on.
    """

    start_column = Column(Integer)
    """
    The column that this declaration begins on.
    """

    end_line = Column(Integer)
    """
    The line that this declaration ends on.
    """

    end_column = Column(Integer)
    """
    The column that this declaration ends on.
    """

    is_array = Column(Boolean)
    """
    Whether or not this declaration is for an array type.
    """

    size = Column(Integer)
    """
    The size of the declared variable, in bytes.
    """

    def __repr__(self):
        return f"<VarDecl {self.type_} {self.name}>"


class Call(Base):
    """
    Represents a function call.
    """

    __tablename__ = "calls"

    id = Column(Integer, primary_key=True)
    """
    This call's database ID.
    """

    function_id = Column(Integer, ForeignKey("functions.id"))
    """
    The ID of the `Function` that this call is present in.
    """

    function = relationship("Function", back_populates="calls")
    """
    The `Function` that this call is present in.
    """

    expr = Column(String)
    """
    The call expression itself.
    """

    name = Column(String)
    """
    The name of the callee.
    """

    start_line = Column(Integer)
    """
    The line that this call begins on.
    """

    start_column = Column(Integer)
    """
    The column that this call begins on.
    """

    end_line = Column(Integer)
    """
    The line that this call ends on.
    """

    end_column = Column(Integer)
    """
    The column that this call ends on.
    """

    arguments = relationship("Argument")
    """
    The `Argument`s associated with this call.
    """

    def __repr__(self):
        return f"<Call {self.expr}>"


class Argument(Base):
    """
    Represents an argument to a function call.
    """

    __tablename__ = "call_arguments"

    id = Column(Integer, primary_key=True)
    """
    This argument's database ID.
    """

    call_id = Column(Integer, ForeignKey("calls.id"))
    """
    The ID of the `Call` that this argument is in.
    """

    call = relationship("Call", back_populates="arguments")
    """
    The `Call` that this argument is in.
    """

    name = Column(String)
    """
    The name of the argument.
    """

    type_ = Column(String)
    """
    The type of the argument.
    """

    def __repr__(self):
        return f"<Argument {self.type_} {self.name}>"


class Statement(Base):
    """
    Represents a primitive (i.e., non-compound) C or C++ statment.
    """

    __tablename__ = "statements"

    id = Column(Integer, primary_key=True)
    """
    This statement's database ID.
    """

    module_name = Column(Integer, ForeignKey("modules.name"))
    """
    The name of the `Module` that this statement is in.
    """

    module = relationship("Module", back_populates="statements")
    """
    The `Module` that this statement is in.
    """

    function_id = Column(Integer, ForeignKey("functions.id"))
    """
    The ID of the `Function` that this statement is in.
    """

    function = relationship("Function", back_populates="statements")
    """
    The `Function` that this statement is in.
    """

    start_line = Column(Integer)
    """
    The line that this statement begins on.
    """

    start_column = Column(Integer)
    """
    The column that this statement begins on.
    """

    end_line = Column(Integer)
    """
    The line that this statement ends on.
    """

    end_column = Column(Integer)
    """
    The column that this statement ends on.
    """

    expr = Column(String)
    """
    The expression text of this statement.
    """

    def __repr__(self):
        return f"<Statement {self.expr}>"


class DB:
    """
    A convenience class for querying the database.
    """

    @classmethod
    def create(cls, db_path, echo=False):
        """
        Creates a new database at the given path.
        """

        engine = create_engine(f"sqlite:///{db_path}", echo=echo)

        session = sessionmaker(bind=engine)()
        Base.metadata.create_all(engine)

        return cls(session, db_path)

    def __init__(self, session, db_path):
        self.session = session
        self.db_path = db_path

    def query(self, *args, **kwargs):
        """
        Forwards a SQLAlchemy-style `query` to the database.
        """

        return self.session.query(*args, **kwargs)
