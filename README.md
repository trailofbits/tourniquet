# Tourniquet

![CI](https://github.com/trailofbits/tourniquet/workflows/CI/badge.svg)

A Python library for easy C/C++ syntax guided program transformation/repair.
This is still very early in development.

## Quickstart

Build the library with docker

```bash
$ docker build -t trailofbits/tourniquet .
$ docker run -it trailofbits/tourniquet
```

Enter an `ipython` instance and `import tourniquet`

## Syntax Guided Program Repair TL;DR

Fixing programs is hard, and one of the most popular techniques for automated repair is search. If you're familiar with
fuzzing, it is basically the reverse. In fuzzing you are mutating inputs to cause a crash, but in search based program
repair you are mutating the program until you pass some specific tests.

One huge drawback of this search based approach is that the search space is huge and most mutations in it
are useless. The idea behind syntax guided program repair is to come up with some generally useful syntax patterns and
to use those for your search space. This means your search space is smaller (restricted by the syntax patterns) and
you are focusing on patch candidates that might actually fix whatever bug is in front of you.

## So What Even Is Tourniquet?

Tourniquet is a library and domain specific language for syntax guided program repair. Current tools have
hard coded fix patterns within them, making it hard for humans to interact and tweak them. The goal of Tourniquet is to
make it quick and easy to create repair templates that can immediately be used to try and repair bugs. We plan on using
Tourniquet alongside program analysis tools to allow humans to create fix patterns that have semantic meaning.

## Domain Specific Language

Rather than writing individual tree transform passes or other types of source manipulation, Tourniquet makes it easy to
describe part of the syntax and part of the semantics of a repair and lets the computer do the rest. Here is a simple
example template:

```python
class YourSemanticAnalysis(Expression):
    def concretize(self, _db, _location):
        yield "SOME_ERROR_CONSTANT"


def your_matcher_func(line, col):
    return True


demo_template = PatchTemplate(
    FixPattern(  # Location 1
        IfStmt(
            LessThanExpr(Variable(), Variable()),  # Location 2
            NodeStmt()  # Location 3
        ),
        ElseStmt(
            ReturnStmt(YourSemanticAnalysis())  # Location 4
        )
    ),
    your_matcher_func  # Location 5
)
```

*Location 1* is the beginning of the `FixPattern`. The `FixPattern` describes the overall shape of
the repair. This means the human provides part of the syntax, and part of the semantics of the
repair.

*Location 2* shows some of the different types in the DSL. What this line is describing is a less
than statement with two variables, all the variable information is automatically extracted from the
Clang AST.

*Location 3* is whatever source was matched by your matcher function, also extracted from the
Clang AST.

*Location 4* is an example of how you could integrate program analysis tools with Tourniquet.
The `FixPattern` is trying to do a basic `if...else` statement where the `else` case returns some
value. Return values have semantic properties, returning some arbitrary integer isn't usually a
good idea. This means you can use some program analysis technique to
infer what an appropriate return code might actually be, or simply ask a human to intervene.

*Location 5* is for a matcher. The matcher is a callable that is supposed to
take source line and column information and return `True` or `False` if the `FixPatern` is
applicable to that source location. The idea here is that we couple specific types of fixes with
specific types of bugs. We intend to use some other tools
(such as [Manticore](https://github.com/trailofbits/manticore)) to help determine bug classes.

## Using Tourniquet

```python
# Create a new Tourniquet instance
demo = Tourniquet("test.db")

# Extract info from its AST into the database
demo.collect_info("demo_prog.c")

# Create a new patch template
demo_template = PatchTemplate(
    FixPattern(
        IfStmt(
            LessThanExpr(Variable(), Variable()),
            NodeStmt()
        )
    ),
    lambda x, y: True,
)

# Add the template to the tourniquet instance
demo.register_template("demo_template", demo_template)

# Tell Tourniquet you want to see results from this program, with this template,
# matching against some location
location = Location("demo_prog.c", SourceCoordinate(44, 3))
samples = demo.concretize_template("demo_template", location)

# Look at all the patch candidates!
print(list(samples))

# Attempt to automatically repair the program using that template
# Specify the file, some testcases, and the location information again
demo.auto_patch(
    "demo_template"
    [
        ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 1),
        ("password", 0)
    ],
    location
)
```

Auto patch will return `True` or `False` depending on if you successfully found a patch to fix all testcases. Eventually
we will support having a test case directory etc, this is still early in development.

Check out tourniquet's [API documentation](https://trailofbits.github.io/tourniquet) for more details.

## Development

Install venv to be able to run `make` commands

```bash
$ docker build -t trailofbits/tourniquet .
$ docker run -it trailofbits/tourniquet
root@b9f3a28655b6:/tourniquet# apt-get install -y python3-venv
root@b9f3a28655b6:/tourniquet# python3 -m venv env
root@b9f3a28655b6:/tourniquet# make test
```

## Contributors

* Carson Harmon (carson.harmon@trailofbits.com)
* Evan Sultanik (evan.sultanik@trailofbits.com)
* William Woodruff (william@trailofbits.com)

## Acknowledgements

The project or effort depicted is sponsored by the Air Force Research Laboratory (AFRL) and
DARPA under contract FA8750-19-C-0004. Any opinions, findings and conclusions or recommendations
expressed in this material are those of the author(s) and do not necessarily reflect the views of
the Air Force Research Laboratory (AFRL) and DARPA.

Distribution Statement: Approved for Public Release, Distribution Unlimited
