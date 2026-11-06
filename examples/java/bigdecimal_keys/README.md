# BigDecimal keys: equals, compareTo and scale

**Author: Sandeep Belgavi**

A runnable companion to *BigDecimal Keys in Java: Why 12.50 and 12.5 Are Two Entries in a HashMap*
(aicassindra.com, Java). `BigDecimalKeys.java` prints how `equals`, `compareTo`, `HashSet`, `TreeSet`,
`HashMap`, `stripTrailingZeros`, arithmetic and the `double` constructor treat scale, and defines a `Price`
record that normalises every key to two decimal places with `RoundingMode.UNNECESSARY`, so 12.5 finds the band
loaded as 12.50 and 12.505 is refused instead of silently rounded. Prices are synthetic Belgavi's Book Store
list prices.

## Prerequisites

- A JDK 17 or newer (records). Tested with javac and java 23.0.2. No build tool and no dependencies.
- `.env.example` documents that nothing is read from the environment.

## Commands

From this directory:

```
javac --release 17 -d build BigDecimalKeys.java BigDecimalKeysTest.java
java -cp build BigDecimalKeysTest
java -cp build BigDecimalKeys
```

## Expected output

`BigDecimalKeysTest` prints `14 checks passed` and exits 0. `BigDecimalKeys` prints:

```
equals=false
compareTo=0
hashSetSize=2
treeSetSize=1
rawMapLookup=null
priceKeyLookup=band A
strip100=1E+2
strip100Plain=100
multiply=1.2100
add=12.50
doubleConstructor=0.1000000000000000055511151231257827021181583404541015625
setOfTwoScales=2
```

## Limitations

The checks use plain `main` methods rather than JUnit so the example needs nothing but a JDK. Database and JSON
round trips are described in the article but not exercised here; a two-decimal `Price` suits fixed-scale money
only, not measurements where the scale carries meaning.
