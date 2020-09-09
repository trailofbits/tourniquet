from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class SourceCoordinate:
    """
    Encapsulates the bare amount of state required to uniquely locate
    a source feature within *some* unspecified source file.
    """

    line: int
    """
    The line that the feature occurs on.
    """

    column: int
    """
    The column that the feature occurs on.
    """


@dataclass(frozen=True)
class Location:
    """
    Encapsulates the bare amount of state required to uniquely locate a source
    feature within a program's source code.

    Observe that `Location` does not represent "spans," i.e. the start and end
    lines and columns for a source feature. This is intentional.
    """

    filename: Path
    """
    The path to the file that the feature occurs in.
    """

    coordinates: SourceCoordinate
    """
    The coordinates (line and column) of the feature.

    See also `line` and `column`.
    """

    @property
    def line(self) -> int:
        """
        Returns the line that the feature occurs on.
        """
        return self.coordinates.line

    @property
    def column(self) -> int:
        """
        Returns the column that the feature occurs on.
        """
        return self.coordinates.column


class Locator(ABC):
    """
    Represents an abstract "locator," which can be concretized into a
    iterator of unique source locations.
    """

    @abstractmethod
    def concretize(self) -> Iterator[Location]:
        ...


class TrivialLocator(Locator):
    """
    A trivial locator that just forwards a single unique source location.
    """

    def __init__(self, filename, line, column):
        self._filename = Path(filename)
        self._line = line
        self._column = column

    def concretize(self) -> Iterator[Location]:
        yield Location(self._filename, SourceCoordinate(self._line, self._column))
