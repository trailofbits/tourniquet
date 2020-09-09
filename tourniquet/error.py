class Error(Exception):
    """
    A base error for all tourniquet exceptions.
    """

    pass


class TemplateError(Error):
    """
    A base error for template-related tourniquet exceptions.
    """

    pass


class TemplateNameError(TemplateError):
    """
    Raised whenever a template name conflict or name lookup failure occurs.
    """

    pass


class ASTError(Error):
    """
    A base error for AST-related tourniquet exceptions.
    """

    pass


class PatchSituationError(ASTError):
    """
    Raised whenever a patch can't be situated at the requested location.
    """


class PatchConcretizationError(ASTError):
    """
    Raised whenever a PatchLang expression can't be concretized against the AST.
    """

    pass


# TODO(ww): Think about errors for location concretization.
