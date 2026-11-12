// Author: Sandeep Belgavi. Week-based-year versus calendar year in java.time and SimpleDateFormat.
import java.text.SimpleDateFormat;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.time.temporal.IsoFields;
import java.time.temporal.WeekFields;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.TimeZone;

public final class WeekYear {
    private WeekYear() {}

    /** Formats one date with a pattern under an explicit locale (java.time). */
    public static String fmt(LocalDate d, String pattern, Locale locale) {
        return DateTimeFormatter.ofPattern(pattern, locale).format(d);
    }

    /** Same with the legacy SimpleDateFormat, in UTC so the result does not depend on the machine zone. */
    public static String legacy(LocalDate d, String pattern, Locale locale) {
        SimpleDateFormat f = new SimpleDateFormat(pattern, locale);
        f.setTimeZone(TimeZone.getTimeZone("UTC"));
        return f.format(Date.from(d.atStartOfDay(ZoneOffset.UTC).toInstant()));
    }

    public static Map<String, String> probe() {
        Map<String, String> out = new LinkedHashMap<>();
        LocalDate[] dates = {LocalDate.of(2026, 12, 26), LocalDate.of(2026, 12, 27), LocalDate.of(2026, 12, 31),
                LocalDate.of(2027, 1, 1), LocalDate.of(2027, 1, 3), LocalDate.of(2027, 1, 4)};
        for (LocalDate d : dates) {
            out.put(d + " yyyy US", fmt(d, "yyyy-MM-dd", Locale.US));
            out.put(d + " YYYY US", fmt(d, "YYYY-MM-dd", Locale.US));
            out.put(d + " YYYY UK", fmt(d, "YYYY-MM-dd", Locale.UK));
            out.put(d + " legacy YYYY US", legacy(d, "YYYY-MM-dd", Locale.US));
            out.put(d + " ISO week", d.get(IsoFields.WEEK_BASED_YEAR) + "-W" + d.get(IsoFields.WEEK_OF_WEEK_BASED_YEAR));
            out.put(d + " US week", d.get(WeekFields.of(Locale.US).weekBasedYear()) + "-W" + d.get(WeekFields.of(Locale.US).weekOfWeekBasedYear()));
        }
        out.put("2027-12-31 yyyy vs YYYY ISO", fmt(LocalDate.of(2027, 12, 31), "yyyy", Locale.UK) + " vs " + fmt(LocalDate.of(2027, 12, 31), "YYYY", Locale.UK));
        out.put("2027-01-01 YYYY UK", fmt(LocalDate.of(2027, 1, 1), "YYYY", Locale.UK));
        out.put("2027-01-01 uuuu", fmt(LocalDate.of(2027, 1, 1), "uuuu", Locale.UK));
        out.put("ISO_WEEK_DATE 2026-12-28", DateTimeFormatter.ISO_WEEK_DATE.format(LocalDate.of(2026, 12, 28)));
        out.put("ISO_WEEK_DATE 2027-01-01", DateTimeFormatter.ISO_WEEK_DATE.format(LocalDate.of(2027, 1, 1)));
        return out;
    }

    /** Lists every date in [from, to] where the pattern pair disagrees, the check a CI test can run. */
    public static java.util.List<LocalDate> disagreements(LocalDate from, LocalDate to, Locale locale) {
        java.util.List<LocalDate> bad = new java.util.ArrayList<>();
        for (LocalDate d = from; !d.isAfter(to); d = d.plusDays(1)) {
            if (!fmt(d, "yyyy", locale).equals(fmt(d, "YYYY", locale))) bad.add(d);
        }
        return bad;
    }

    public static void main(String[] args) {
        probe().forEach((k, v) -> System.out.println(k + " = " + v));
        for (int y = 2024; y <= 2030; y++) {
            System.out.println(y + "/" + (y + 1) + " US disagreements: " + disagreements(LocalDate.of(y, 12, 20), LocalDate.of(y + 1, 1, 10), Locale.US));
            System.out.println(y + "/" + (y + 1) + " UK disagreements: " + disagreements(LocalDate.of(y, 12, 20), LocalDate.of(y + 1, 1, 10), Locale.UK));
        }
    }
}
