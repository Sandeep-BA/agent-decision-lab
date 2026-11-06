import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

/**
 * BigDecimal keys: equals compares value and scale, compareTo only value.
 * Author: Sandeep Belgavi. Companion to "BigDecimal Keys in Java: Why 12.50 and 12.5 Are Two Entries in a HashMap"
 * (aicassindra.com). JDK only; prices are synthetic Belgavi's Book Store list prices.
 */
public final class BigDecimalKeys {

  /** A price key that cannot hold two scales: 12.5 becomes 12.50, 12.505 is refused instead of rounded. */
  public record Price(BigDecimal amount) {
    public Price {
      amount = amount.setScale(2, RoundingMode.UNNECESSARY);
    }

    public static Price of(String text) {
      return new Price(new BigDecimal(text));
    }
  }

  static Map<String, Object> probe() {
    BigDecimal db = new BigDecimal("12.50");
    BigDecimal feed = new BigDecimal("12.5");
    Set<BigDecimal> hash = new HashSet<>(List.of(db));
    hash.add(feed);
    Set<BigDecimal> tree = new TreeSet<>(List.of(db));
    tree.add(feed);
    Map<BigDecimal, String> bands = new HashMap<>(Map.of(db, "band A"));
    Map<Price, String> priceBands = new HashMap<>(Map.of(new Price(db), "band A"));
    Map<String, Object> out = new java.util.LinkedHashMap<>();
    out.put("equals", db.equals(feed));
    out.put("compareTo", db.compareTo(feed));
    out.put("hashSetSize", hash.size());
    out.put("treeSetSize", tree.size());
    out.put("rawMapLookup", bands.get(feed));
    out.put("priceKeyLookup", priceBands.get(Price.of("12.5")));
    out.put("strip100", new BigDecimal("100").stripTrailingZeros().toString());
    out.put("strip100Plain", new BigDecimal("100").stripTrailingZeros().toPlainString());
    out.put("multiply", new BigDecimal("1.10").multiply(new BigDecimal("1.10")).toString());
    out.put("add", feed.add(new BigDecimal("0.00")).toString());
    out.put("doubleConstructor", new BigDecimal(0.1).toString());
    out.put("setOfTwoScales", Set.of(new BigDecimal("1.0"), new BigDecimal("1.00")).size());
    return out;
  }

  public static void main(String[] args) {
    probe().forEach((k, v) -> System.out.println(k + "=" + v));
  }
}
