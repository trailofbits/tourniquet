from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class SourceCoordinate:
    line: int
    column: int


@dataclass(frozen=True)
class Location:
    """
    Encapsulates the bare amount of state required to uniquely locate a source
    feature within a program's source code.

    Observe that `Location` does not represent "spans," i.e. the start and end
    lines and columns for a source feature. This is intentional.
    """

    filename: Path
    coordinates: SourceCoordinate

    @property
    def line(self):
        return self.coordinates.line

    @property
    def column(self):
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
