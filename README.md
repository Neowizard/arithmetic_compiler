# Arithmetic Compiler
This is little project to is meant as a tip-of-the-iceberg demonstration 
of parsing and code-generation (with hopes to grow it into a full compiler
pipeline in the future, by adding a semantic analyzer and IR stage)

The code compiles high-level arithmetic expressions into assembly (Intel syntax)
which can be further compiled with GCC to produce an X86_64 executable

## Installation
This project doesn't have an installation script or anything, but it also simple
enough to get away with it.

To run it, there are no dependencies. Testing requires only `pytest` which can easily 
be installed with `pip install pytest` or any package manager of your liking.

## Running
You run the compiler by giving it an input file path and an output file path:

```
$ cat example.in
r11 = 32;
r10 = 0 - r11 / r11;            # r10 = -1
loop r11 {                      # loop r11 (32) times
r10 = r10*2;
}                               # r10 = -4294967296 (-(2**32))

r10 = 15; r11 = 10; r12 = 5;
r13 = r10-r11 / r12;            # Conforming to arithmetic order of precedence, r13 = 13

./main.py example.in example.s
```

This command will compile `example.in` and produce the `example.s` file. 
To further compile&link the assembly code down to an executable you can use
`nasm` and `gcc` like so:
```
nasm -f elf64 ./example.s -o ./example.o
gcc -no-pie ./example.o -o example
``` 

And then execute `example` to get the value of every top-level expression (the value of a loop
is the value of the loop's expression after the last iteration):
```
$ ./example 
32
-1
-4294967296
15
10
5
13
```

## Syntax

You can find the syntax for the arithmetic language in [syntax.bnd](compiler/syntax.bnf) in BNF format. 
Note that the syntax does not include whitespaces. A whitespace is either a line-comment 
(starting with '#') or any char whose ASCII value is <= 32.

We implemented the parser using the Parser Combinators technique. You can find our Parser 
Combinators package in [pc.py](infra/pc.py)

