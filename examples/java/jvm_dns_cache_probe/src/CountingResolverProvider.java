// Author: Sandeep Belgavi. Counting InetAddressResolverProvider (JEP 418) for measuring the JDK name cache.
import java.net.*;
import java.net.spi.*;
import java.util.*;
import java.util.concurrent.atomic.*;
import java.util.stream.*;

public class CountingResolverProvider extends InetAddressResolverProvider {
    public static final AtomicInteger CALLS = new AtomicInteger();
    public static final List<String> LOG = Collections.synchronizedList(new ArrayList<>());
    public static volatile long start = System.nanoTime();
    public static volatile boolean failing = false;
    public static volatile int answer = 10;

    @Override public InetAddressResolver get(Configuration c) {
        InetAddressResolver builtin = c.builtinResolver();
        return new InetAddressResolver() {
            @Override public Stream<InetAddress> lookupByName(String host, LookupPolicy p) throws UnknownHostException {
                if (!host.endsWith(".bookstore.test")) return builtin.lookupByName(host, p);
                int n = CALLS.incrementAndGet();
                long ms = (System.nanoTime() - start) / 1_000_000;
                LOG.add(String.format("resolver call %d at %.1f s for %s", n, ms / 1000.0, host));
                if (failing || host.startsWith("missing")) throw new UnknownHostException(host);
                return Stream.of(InetAddress.getByAddress(host, new byte[]{10, 0, 0, (byte) answer}));
            }
            @Override public String lookupByAddress(byte[] a) throws UnknownHostException { return builtin.lookupByAddress(a); }
        };
    }
    @Override public String name() { return "counting-bookstore-resolver"; }
}
