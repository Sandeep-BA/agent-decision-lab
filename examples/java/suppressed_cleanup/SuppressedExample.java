// Author: Sandeep Belgavi. Original synthetic cleanup failure example.
public class SuppressedExample {
    static final class Resource implements AutoCloseable {
        private final String name;
        Resource(String name) { this.name = name; }
        @Override public void close() {
            throw new IllegalStateException("close:" + name);
        }
    }
    public static void main(String[] args) {
        try (var input = new Resource("input");
             var output = new Resource("output")) {
            throw new IllegalArgumentException("body:invalid fixture");
        } catch (RuntimeException failure) {
            assert failure.getMessage().equals("body:invalid fixture");
            Throwable[] secondary = failure.getSuppressed();
            assert secondary.length == 2;
            assert secondary[0].getMessage().equals("close:output");
            assert secondary[1].getMessage().equals("close:input");
            System.out.println(failure.getMessage());
            for (Throwable item : secondary) {
                System.out.println("suppressed:" + item.getMessage());
            }
        }
    }
}
