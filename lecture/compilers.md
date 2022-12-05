# Introduction

What's a compiler? I'll start with what a compiler is not (necessarily). 

1. A compiler is not (necessarily) a program that creates an executable
1. A compiler is not (necessarily) a program that translates code into assembly
1. A compiler does not calculate the value of an expression/the input code (except in very few, small and special cases)

A compiler is a program that translates source code in one language, into source code in another language. For instance
`javac` compiles Java source code into ByteCode, `gcc` compiles C into assembly (among others) and `bison` compiles CFG 
specifications (written as Bison Grammar) to C.

It's important to distinguish between a compiler that translates code from one language to another, and an interpreter 
that evaluates code (where the CPU is the "final interpreter" in every tool-chain).

# Why Compile?
If compilers just translate code from one language to another, why do we need them? We can implement interpreters to 
actually evaluate the code for any language on any architecture. What's the compiler's role? **Optimizations**. A 
compiler is first and foremost a platform on top of which we implement optimizations. In the last few decades compilers
developers have also begun to emphasise code analyses to give the user more insight and warn against potentially 
troublesome code. 

A compiler exists so that developers can write good code from a software engineering standpoint, while ignoring any 
questions of how the code performs. The compiler is tasked with taking that well engineered, but poorly performing, code
and transforming it to its most optimized form in the target language.

For instance, if we write the following code:
```c
for (int i = 0; i < rows; i++) {
    for (int j = 0; j < cols; j ++) {
        arr[i][j] = foo(i, j);
    }
}
```
A smart optimizing compiler would produce:
```c
for (int i = 0; i < rows; i++) {
    row = arr[i];
    for (int j = 0; j < cols; j ++) {
        row[j] = foo(i, j);
    }
}
``` 

And a really smart compiler would produce:
```c
for (int i = 0; i < rows; i++) {
    row = arr[i];
    row_foo = partial_foo(i);   // row_foo executes the part of foo that depends on j
                                // partial_foo executes the part that depends on i
    for (int j = 0; j < cols; j ++) {
        row[j] = row_foo(j);
    }
}
```
Consider, for example, that foo could be taking the root of `i` and multiplying it by `j`. Or that we read a file pointed at by `i`, and searching within its contents the string `j`. Avoiding the cost of what `foo` does with `i` again and again, `cols` times, can be a significant optimization.

We wouldn't want to perform this optimization in our source, since it would cause both `partial_foo` and its resulting
partial function `row_foo` to be extremely coupled, and both functions would be horrible to maintain since they 
inherently contain only half the task. 

Note, this technique of implementing a function partially and returning the rest of calculation is called "currying" 
after Haskell Curry who invented it. It's implemented natively in some languages like Ocaml, Reason and F#.

 
## What can we optimize?
We all intuitively thing about runtime and memory when we think about optimizations, and for the most part, that's 
accurate. Most compilers are focused with optimizing CPU performance, and (to a lesser degree) memory utilization.

However, any finite resource can be optimized. There are compilers that can reduce the size of the executable, the 
startup time, the number of registers used during execution, IO, CPU idle time, context switches and just about any
resource we can consider.

However, there are also compilers that control the code's layout (formatters are a subclass of these compilers), 
the line-length and various other visual aspects. These compilers try to optimize the coder's attention. Reducing 
interruptions and confusion.

There are compilers that are tasked with optimizing the runtime of CNC machines since those are usually slow 
(relatively) and their time is very expensive.    
 
# Compiler pipeline

This is the traditional pipeline for a compiler:
![Pipeline](pipeline.svg)

The traditional compiler pipeline is not the only design for a compiler, and in fact most compilers are not implemented
exactly this way. Some stages are often added while some can be omitted.

### Scanner
The scanner is responsible for taking the source input, and chunking it up into atomic chunks of information, tokens.

A token can be the "if" keyword, the number 6.283, a curly bracket etc. The 'i' character in "int" is not a token since
it has no meaning in its own right. It's only a part of the "int" token.

Whitespaces and comments are not tokens and are either ignored or used to separate tokens.

The scanner is defined using a set of regular expressions, where each expression usually corresponds to a type of token.

Note, the compiler exampled in this repo does not implement a scanner. The parser takes, as its token list, a string
where each char in the string is a token.

### Parser
The parser is responsible to detecting the hierarchical relationship between tokens and build the *Abstract Syntax
Tree* from that relationship.

An Abstract Syntax is the internal representation the compiler defines for different syntactic elements in the source 
language. For instance, a `function` can be defined as an object like so:
```python
class FunctionNode(AstNode):
    parameters: (TypeNode, str)
    ReturnType: TypeNode
    Body: list[StatementNode]
```
Which shows the hierarchy between a function and its body. 

The parser is also in charge of implementing syntactic sugars. A syntactic sugar is a bit of syntax that has no AST node
designed to describe it, and it's instead parsed into one or more nodes of other syntactic elements. The most ubiquitous
example of a syntactic sugar is array indexing in C. This syntactic sugar is transformed into a 
set of operations that achieve the same semantics, specifically, an offset-dereference:
```C
arr[3] == *(arr + 3) // Note that pointer arithmetic comes into play here
```

Parsers and Scanners form the frontend of a compiler. Their separation is more a matter of software engineering than 
strictly parsing-theory. Syntax errors are detect by the Parser or the Scanner.

#### Our Parser
We implemented our parser using the Parsers Combinator technique. This technique allows us to implement the syntax
specifications directly in the compiler's language, and so every syntactic element becomes a first-class object in
our code. This makes the parser, small, robust and very easy to upgrade.
 
This so opens the door for a language designer to implement "quality of life" choices into the language, like not 
requiring the user to use curly brackets in loops, or any start-end syntax for loops, while also not being 
whitespace-sensitive.

Our Parser Combinators implementation is heavily inspired by the work done by Dr. Mayer Goldberg 
(http://www.little-lisper.org)

### Semantic Analyzer
The Semantic Analyzer takes the AST and transforms it into the compiler's *Intermediate Representation* (IR). The 
Semantic Analyzer performs various analyses on both the input AST and the output IR. Binding variables to their scopes, 
inferring types, detecting type violations etc.

This stage is the engine behind most optimizations performed by the compiler. There are generalized algorithms used to
implement analyses, like Dataflow Frameworks. These take the IR as well as the analysis definition and enrich the IR.

An IR can be many things. From the input AST all the way up to complete assembly languages. In most cases, the IR will
be a simplified assembly-like language, with most real-world limitations removed (e.g. limited number of registers,
operations side-effects).

Note, the compiler exampled in this repo does not implement a Semantic Analyzer. The IR used by the code generator
is the AST itself.

### Code Generator
The Code Generator takes IR and generates text in the target language that has the same meaning in the target language
as the input code had in the source language.

The code generator responsible for constricting the runtime framework, the internal representation of the source 
language's data types (e.g. representing Python objects in assembly), implementing how functions are invoked,
how variables are stored and accessed, implementing many of the optimizations and, of course, generating the code for 
the IR in the target language.

The Code Generator is the back-end of the compiler

#### Our Code Generator
The Code Generator our exampled compiler is very straight forward. It compiles our IR (AST) down the x86_64 assembly.

All the data in our source language (integers) is native to our target language, so their representation is trivial. 
Since we don't support functions and only a fixed set of variables (r10, r11, r12 and r13), those are also trivial.

In fact, almost every command in our source language has a very simple implementation in our target language, so in fact 
our Code Generator is a straight forward translator for every statement except for the `loop` statement. 

 
