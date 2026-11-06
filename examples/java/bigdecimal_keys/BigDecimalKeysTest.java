import java.math.BigDecimal;
import java.util.Map;

/**
 * Plain-JDK checks for BigDecimalKeys (no test framework). Exit status 1 on the first failure.
 * Author: Sandeep Belgavi.
 */
public final class BigDecimalKeysTest {
  private static int passed = 0;

  private static void check(String name, Object expected, Object actual) {
    if (!java.util.Objects.equals(expected, actual)) {
      System.out.println("FAIL " + name + ": expected " + expected + " but was " + actual);
      System.exit(1);
    }
    passed++;
  }

  public static void main(String[] args) {
    Map<String, Object> r = BigDecimalKeys.probe();
    check("equals compares scale", false, r.get("equals"));
    check("compareTo compares value", 0, r.get("compareTo"));
    check("HashSet keeps both scales", 2, r.get("hashSetSize"));
    check("TreeSet merges them", 1, r.get("treeSetSize"));
    check("raw HashMap lookup misses", null, r.get("rawMapLookup"));
    check("Price key lookup finds the band", "band A", r.get("priceKeyLookup"));
    check("stripTrailingZeros(100)", "1E+2", r.get("strip100"));
    check("toPlainString", "100", r.get("strip100Plain"));
    check("multiply adds scales", "1.2100", r.get("multiply"));
    check("add keeps the larger scale", "12.50", r.get("add"));
    check("double constructor", "0.1000000000000000055511151231257827021181583404541015625", r.get("doubleConstructor"));
    check("Set.of accepts both scales", 2, r.get("setOfTwoScales"));
    try {
      BigDecimalKeys.Price.of("12.505");
      check("12.505 must be refused", "ArithmeticException", "accepted");
    } catch (ArithmeticException expected) {
      passed++;
    }
    check("Price normalises scale", new BigDecimal("12.50"), BigDecimalKeys.Price.of("12.5").amount());
    System.out.println(passed + " checks passed");
  }
}
