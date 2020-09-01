# Tourniquet

A Python library for easy C/C++ syntax guided program transformation/repair.
This is still very early in development.

# Quickstart

Build the library with docker

```bash
$ docker build -t trailofbits/tourniquet .
$ docker run -it trailofbits/tourniquet
```

Enter an `ipython` instance and `import tourniquet`

# Syntax Guided Program Repair TL;DR

Fixing programs is hard, and one of the most popular techniques for automated repair is search. If you're familiar with 
fuzzing, it is basically the reverse. In fuzzing you are mutating inputs to cause a crash, but in search based program
repair you are mutating the program until you pass some specific tests. 

One huge drawback of this search based approach is that the search space is huge and most mutations in it 
are useless. The idea behind syntax guided program repair is to come up with some generally useful syntax patterns and 
to use those from your search space. This means your search space is smaller (restricted by the syntax patterns) and
you are focusing on patch candidates that might actually fix whatever bug is in front of you. 

# So What Even Is Tourniquet? 

Tourniquet is a library and domain specific language for syntax guided program repair. Current tools have
hard coded fix patterns within them, making it hard for humans to interact and tweak them. The goal of Tourniquet is to
make it quick and easy to create repair templates that can immediately be used to try and repair bugs. We plan on using
Tourniquet alongside program analysis tools to allow humans to create fix patterns that have semantic meaning.  

# Domain Specific Language 

Rather than writing individual tree transform passes or other types of source manipulation, Tourniquet makes it easy to 
describe part of the syntax and part of the semantics of a repair and lets the computer do the rest. Here is a simple 
example template: 

```python
demo_template = PatchTemplate("demo_template", # Location 1 
                  your_matcher_function # Location 2 
                  FixPattern( # Location 3
                    IfStmt(
                      LessThanExpr(Variable(), Variable()), # Location 4 
                        NodeStmt() # Location 5
                    ),   
                    ElseStmt(
                        ReturnStmt(your_semantic_analysis) # Location 6
                        )
                    )
                  )
                )	
``` 

*Location 1* describes the name of the template you are creating. 

*Location 2* is for a matcher function. The matcher function is a function that is supposed to take source line and column 
information and return True or False if the FixPatern is applicable to that source location. The idea here is that we 
couple specific types of fixes with specific types of bugs. We intend to use some other tools (such as manticore) to 
help determine bug classes.   

*Location 3* is the beginning of the FixPattern. The FixPattern describes the overall shape of the repair. This means the
human provides part of the syntax, and part of the semantics of the repair. 

*Location 4* shows some of the different types in the DSL. What this line is describing is a less than statement 
with two variables, all the variable information is automatically extracted from the clang AST. 

*Location 5* is whatever source was matched by your matcher function, also extracted from the clang AST. 

*Location 6* is an example of how you could integrate program analysis tools with Tourniquet. The FixPattern is trying
to do a basic if/else statement where the else case returns some value. Return values have semantic properties, 
returning some arbitrary integer isn't usually a good idea. This means you can use some program analysis technique to 
infer what an appropriate return code might actually be, or simply ask a human to intervene. 

# Using Tourniquet

```python
# Create a new Tourniquet instance 
demo = Tourniquet("test.db") 

# Extract info from its AST into the database 
demo.collect_info("your_program.c") 

# Create a new patch template 
demo_template = PatchTemplate("demo_template", 
                        lambda x, y: True,
                        FixPattern(
                            IfStmt(
                    	    LessThanExpr(Variable(), Variable()),
                      	        NodeStmt()
                            )
                        )
                    )

#Add the template to the tourniquet instance 	
demo.add_new_template(demo_template)

# Tell Tourniquet you want to see results from this program, with this template, matching against some location 
samples = demo.concretize_template("demo_prog.c", "demo", 44, 3)

# Look at all the patch candidates! 
print(samples) 

# Attempt to automatically repair the program using that template
# Specify the file, some testcases, and the location information again 
demo.auto_patch("demo_prog.c",
                [
                    ("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", 1),
                    ("password", 0)
                 ],
                "demo",
                44, 3)
```

Auto patch will return `True` or `False` depending on if you successfully found a patch to fix all testcases. Eventually
we will support having a test case directory etc, this is still early in development. 

# Development

Install venv to be able to run `make` commands

```bash
$ docker build -t trailofbits/tourniquet .
$ docker run -it trailofbits/tourniquet
root@b9f3a28655b6:/tourniquet# apt-get install -y python3-venv
root@b9f3a28655b6:/tourniquet# python3 -m venv env
root@b9f3a28655b6:/tourniquet# make test
```

# Contributors

* Carson Harmon (carson.harmon@trailofbits.com)
* Evan Sultanik (evan.sultanik@trailofbits.com)
* William Woodruff (william@trailofbits.com)
