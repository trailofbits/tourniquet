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
