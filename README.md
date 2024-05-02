# JPAMB: Java Program Analysis Micro Benchmarks

The goal of this benchmark suite is to make a collection of interesting
micro-benchmarks to be solved by either dynamic or static analysis.

## Rules of the Game

The goal is to build a program analysis that takes two arguments, a method ID and a query.
A method ID is the fully qualified name of the class, the method name, ":", and 
then the [method descriptor](https://docs.oracle.com/javase/specs/jvms/se22/html/jvms-4.html#jvms-4.3.3), 
for example:
```
jpamb.cases.Simple.assertPositive:(I)V
jpamb.cases.Simple.divideByZero:()I 
```

And the query is one of: 

| query              | description                            |
| :-----             | :-----                                 |
| `assertion error`  | an execution throws an assertion error |
| `ok`               | an execution runs to completion        | 
| `*`                | an execution runs forever              | 
| `divide by zero`   | an execution divides by zero           | 

Your analysis should look like this:

```shell
$> ./analysis "jpamb.cases.Simple.assertPositive:(I)V" "assertion error"
```

In which case it should either reply with a wager, e.i., the number of points
waged [`-inf`, `inf`] on your prediction. A negative wager is against the query, and 
a positive is for the query. A failed wager is subtracted from your points, however 
a successful wager is converted into points like so:
$$\mathtt{points} = 1 - \frac{1}{\mathtt{wager} + 1}$$

If your analysis is queried with an "assertion error" and you are sure that the program does not contain one, 
you can wager -200 points. If you are wrong, and the program can exhibit an assertion error, 
you lose 200 point, but if you are correct, you gain $1 - 1 / 201 = 0.995$ points.

Below are some example values. Note that small wagers equal smaller risk.

|  wager | points |
|   ---: |    ---:|
|   0.00 |   0.00 |
|   0.25 |   0.20 |
|   0.50 |   0.33 |
|   1.00 |   0.50 | 
|   3.00 |   0.75 | 
|   9.00 |   0.90 | 
|  99.00 |   0.99 | 
|    inf |   1.00 | 

Examples of such scripts can be seen in `solutions/`.

### Probabilities

You can also respond with a probabilities [`0%`, `100%`], which is automatically converted into 
the optimal wager. An example of this is in`solutions/apriori.py`, which uses the distribution 
of errors from `stats/distribution.csv` to gain an advantage.

If you are curious, the optimal wager is found by solving the following quadratic function:
$$(1 - p) \mathtt{wager} = p \mathtt{points} = p (1 - \frac{1}{\mathtt{wager} + 1})$$
And dividing by 2 to get the optimal wager:
$$\mathtt{wager} = \frac{1 - 2 p }{2 (p - 1)}$$

|   prob |  wager |
|   ---: |    ---:|
|     0% |   -inf |
|    10% |     -8 |
|    25% |     -2 |
|    50% |      0 |
|    75% |      2 |
|    90% |      8 |
|   100% |    inf | 

## Getting Started

To get started evaluating your tool you can run the `evaluate.py` script, it only requires 
the `click` library and python 3.

```
Usage: evaluate.py [OPTIONS] COMMAND [ARGS]...

  The jpamb evaluator

Options:
  --help  Show this message and exit.

Commands:
  cases     Get a list of cases to test
  evaluate  Given an command check if it can predict the results.
  rebuild   Rebuild the benchmark-suite.
  test      Check that all cases are valid
```

To evaluate your analysis you should be able to simply run:
```shell
$> ./evaluate.py evaluate <your-analysis>
```

There are more interesting options:

```shell
Usage: evaluate.py evaluate [OPTIONS] [CMD]...

  Given an command check if it can predict the results.

Options:
  --timeout FLOAT
  --fail-fast
  -v
  --queries TEXT     [default: *, assertion error, divide by zero, ok]
  --workfolder PATH  [default: /Users/chrg/Develop/repos/jpamb]
  --help             Show this message and exit.
```

If you have problems getting started, please file an [issue](https://github.com/kalhauge/jpamb/issues).

### Source code

The source code is located under the `src/main/java`. 
A simple solution that analyze the source code directly using the [tree-sitter
library](https://tree-sitter.github.io/tree-sitter/) is located at
`solutions/syntaxer.py`.

### Byte code

To write more advanced analysis it makes sense to make use of the byte-code. To
lower the bar to entrance, the byte code of the benchmarks have already been decompiled by the 
[`jvm2json`](https://github.com/kalhauge/jvm2json) tool. 
The codec for the output is described [here](https://github.com/kalhauge/jvm2json/blob/main/CODEC.txt).

Some sample code for how to get started can be seen in `solutions/bytecoder.py`.

## Developing

The easiest way to get started is to install java, maven, and python3 with `click` installed.

