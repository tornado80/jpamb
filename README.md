# JPAMB: Java Program Analysis Micro Benchmarks

The goal of this benchmark suite is to make a collection of interesting
micro-benchmarks to be solved by either dynamic or static analysis.

## Getting started

To get started using the framework, you first have to build a wrapper script around 
your program analysis that takes two arguments, a method ID and a query.
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

Here are some example values:

| wager | points |
|  ---: |    ---:|
|     0 |   0.00 |
|     1 |   0.50 | 
|     3 |   0.75 | 
|     9 |   0.90 | 
|    99 |   0.99 | 
|   inf |   1.00 | 

### Probabilities

One can also respond with a probability [0%,100%], which is automatically converted into 
the optimal wager.

## Developing

The easiest way to get started is to install java, maven, and python3 with `click` installed.

If you have problems getting started, please file an [issue](https://github.com/kalhauge/jpamb/issues).

### Using nix

You

