import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

/**
 * Default-locale bugs in case mapping and number formatting, reproduced with plain JDK calls.
 * Author: Sandeep Belgavi. No dependencies; all inputs are synthetic.
 */
public final class LocaleCase {
  enum Status { PENDING_REVIEW, PAID, REFUNDED }

  static final Locale TR = Locale.forLanguageTag("tr-TR");
  static final Locale DE = Locale.forLanguageTag("de-DE");

  /** The buggy pattern: case mapping that silently uses the JVM default locale. */
  static Status parseStatusDefault(String s) {
    return Status.valueOf(s.toUpperCase());
  }

  /** The fix: locale-neutral case mapping for identifiers, protocol tokens and keys. */
  static Status parseStatusRoot(String s) {
    return Status.valueOf(s.toUpperCase(Locale.ROOT));
  }

  static Map<String, String> probe() {
    Map<String, String> r = new LinkedHashMap<>();
    Locale saved = Locale.getDefault();
    try {
      Locale.setDefault(TR);
      r.put("upperDefaultTr", "title".toUpperCase());
      r.put("upperRoot", "title".toUpperCase(Locale.ROOT));
      r.put("lowerDefaultTr", "X-REQUEST-ID".toLowerCase());
      r.put("lowerRoot", "X-REQUEST-ID".toLowerCase(Locale.ROOT));
      r.put("equalsIgnoreCase", String.valueOf("title".equalsIgnoreCase("TITLE")));
      r.put("headerMatchDefault", String.valueOf("X-REQUEST-ID".toLowerCase().equals("x-request-id")));
      try {
        r.put("enumDefault", parseStatusDefault("pending_review").name());
      } catch (IllegalArgumentException e) {
        r.put("enumDefault", "IllegalArgumentException");
      }
      r.put("enumRoot", parseStatusRoot("pending_review").name());
      Locale.setDefault(DE);
      r.put("formatDefaultDe", String.format("%.2f", 12.5));
      r.put("formatRoot", String.format(Locale.ROOT, "%.2f", 12.5));
      r.put("upperSharpS", "stra\u00dfe".toUpperCase(Locale.ROOT));
      r.put("upperSharpSLength", String.valueOf("stra\u00dfe".toUpperCase(Locale.ROOT).length()));
    } finally {
      Locale.setDefault(saved);
    }
    return r;
  }

  public static void main(String[] args) {
    for (Map.Entry<String, String> e : probe().entrySet()) {
      System.out.println(e.getKey() + "=" + escape(e.getValue()));
    }
  }

  /** Print non-ASCII as Unicode escapes so the output is the same on every console code page. */
  static String escape(String s) {
    StringBuilder b = new StringBuilder();
    for (char c : s.toCharArray()) {
      if (c < 128) b.append(c); else b.append(String.format(Locale.ROOT, "\\u%04X", (int) c));
    }
    return b.toString();
  }
}
