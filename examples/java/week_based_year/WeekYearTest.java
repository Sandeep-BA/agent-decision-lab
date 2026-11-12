// Author: Sandeep Belgavi. Plain-JDK checks for WeekYear; no test framework needed.
import java.time.LocalDate;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public final class WeekYearTest {
    private static int passed = 0;

    private static void eq(Object expected, Object actual, String what) {
        if (!expected.equals(actual)) throw new AssertionError(what + ": expected " + expected + " but got " + actual);
        passed++;
    }

    public static void main(String[] args) {
        Map<String, String> p = WeekYear.probe();
        eq("2026-12-26", p.get("2026-12-26 YYYY US"), "Saturday before the US week turns over");
        eq("2027-12-27", p.get("2026-12-27 YYYY US"), "US week 1 of 2027 starts Sunday 27 December 2026");
        eq("2027-12-31", p.get("2026-12-31 YYYY US"), "New Year's Eve in the US locale");
        eq("2027-12-31", p.get("2026-12-31 legacy YYYY US"), "SimpleDateFormat agrees with java.time for US");
        eq("2026-12-31", p.get("2026-12-31 YYYY UK"), "UK uses ISO weeks; 31 December 2026 is in 2026-W53");
        eq("2026-01-03", p.get("2027-01-03 YYYY UK"), "UK: 3 January 2027 still belongs to week-based-year 2026");
        eq("2026-W53", p.get("2027-01-01 ISO week"), "ISO week of 1 January 2027");
        eq("2027-W1", p.get("2027-01-04 ISO week"), "first ISO week of 2027 starts Monday 4 January");
        eq("2026-W53-1", p.get("ISO_WEEK_DATE 2026-12-28"), "ISO week date formatter");
        eq("2027", p.get("2027-01-01 uuuu"), "uuuu is the proleptic calendar year");
        List<LocalDate> us = WeekYear.disagreements(LocalDate.of(2026, 12, 20), LocalDate.of(2027, 1, 10), Locale.US);
        eq(5, us.size(), "US disagreement days around New Year 2027");
        List<LocalDate> uk = WeekYear.disagreements(LocalDate.of(2026, 12, 20), LocalDate.of(2027, 1, 10), Locale.UK);
        eq(List.of(LocalDate.of(2027, 1, 1), LocalDate.of(2027, 1, 2), LocalDate.of(2027, 1, 3)), uk, "UK disagreement days");
        eq(0, WeekYear.disagreements(LocalDate.of(2027, 2, 1), LocalDate.of(2027, 11, 30), Locale.US).size(), "no disagreement mid-year");
        System.out.println(passed + " checks passed");
    }
}
