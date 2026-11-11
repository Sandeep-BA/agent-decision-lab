import java.util.Map;
import java.util.Objects;

/**
 * Plain-JDK checks for LocaleCase (no test framework). Exit status 1 on the first failure.
 * Author: Sandeep Belgavi.
 */
public final class LocaleCaseTest {
  private static int passed = 0;

  private static void check(String name, Object expected, Object actual) {
    if (!Objects.equals(expected, actual)) {
      System.out.println("FAIL " + name + ": expected " + expected + " but was " + actual);
      System.exit(1);
    }
    passed++;
  }

  public static void main(String[] args) {
    java.util.Locale before = java.util.Locale.getDefault();
    Map<String, String> r = LocaleCase.probe();
    check("dotted capital I under tr", "T\u0130TLE", r.get("upperDefaultTr"));
    check("root upper", "TITLE", r.get("upperRoot"));
    check("dotless small i under tr", "x-request-\u0131d", r.get("lowerDefaultTr"));
    check("root lower", "x-request-id", r.get("lowerRoot"));
    check("equalsIgnoreCase is locale independent", "true", r.get("equalsIgnoreCase"));
    check("header comparison fails under tr", "false", r.get("headerMatchDefault"));
    check("enum lookup fails under tr", "IllegalArgumentException", r.get("enumDefault"));
    check("enum lookup with ROOT", "PENDING_REVIEW", r.get("enumRoot"));
    check("decimal comma under de", "12,50", r.get("formatDefaultDe"));
    check("decimal point with ROOT", "12.50", r.get("formatRoot"));
    check("sharp s expands", "STRASSE", r.get("upperSharpS"));
    check("length changes", "7", r.get("upperSharpSLength"));
    check("default locale restored", before, java.util.Locale.getDefault());
    System.out.println(passed + " checks passed");
  }
}
