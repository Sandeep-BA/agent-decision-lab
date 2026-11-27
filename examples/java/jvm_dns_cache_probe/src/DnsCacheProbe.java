// Author: Sandeep Belgavi. Measures how often InetAddress consults the resolver under different cache properties.
import java.net.*;
import java.security.Security;

public class DnsCacheProbe {
    public static void main(String[] args) throws Exception {
        String scenario = args[0];
        int seconds = Integer.parseInt(args[1]);
        if (args.length > 2 && !args[2].equals("-")) Security.setProperty("networkaddress.cache.ttl", args[2]);
        if (args.length > 3 && !args[3].equals("-")) Security.setProperty("networkaddress.cache.negative.ttl", args[3]);
        if (args.length > 4 && !args[4].equals("-")) Security.setProperty("networkaddress.cache.stale.ttl", args[4]);
        int failAt = args.length > 5 ? Integer.parseInt(args[5]) : -1;
        String host = scenario.equals("negative") ? "missing.bookstore.test" : "orders.bookstore.test";
        CountingResolverProvider.start = System.nanoTime();
        int ok = 0, failed = 0;
        for (int t = 0; t < seconds; t++) {
            if (failAt >= 0 && t == failAt) { CountingResolverProvider.failing = true; System.out.println("resolver starts failing at " + t + " s"); }
            try { InetAddress a = InetAddress.getByName(host); ok++; if (t % 5 == 0 || failAt >= 0) System.out.println("t=" + t + " s -> " + a.getHostAddress()); }
            catch (UnknownHostException e) { failed++; if (t % 5 == 0 || failAt >= 0) System.out.println("t=" + t + " s -> UnknownHostException"); }
            Thread.sleep(1000);
        }
        CountingResolverProvider.LOG.forEach(System.out::println);
        System.out.println("scenario=" + scenario + " lookups=" + seconds + " ok=" + ok + " failed=" + failed + " resolverCalls=" + CountingResolverProvider.CALLS.get());
    }
}
