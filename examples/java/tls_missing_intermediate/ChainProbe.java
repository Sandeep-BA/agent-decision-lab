// Author: Sandeep Belgavi. Original teaching example: a TLS server that omits its
// intermediate certificate, and a Java client that trusts only the root.
import com.sun.net.httpserver.HttpsConfigurator;
import com.sun.net.httpserver.HttpsServer;
import java.io.FileInputStream;
import java.io.InputStream;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.security.PrivateKey;
import java.security.cert.Certificate;
import java.security.cert.CertificateFactory;
import java.time.Duration;
import javax.net.ssl.KeyManagerFactory;
import javax.net.ssl.SSLContext;
import javax.net.ssl.SSLHandshakeException;
import javax.net.ssl.TrustManagerFactory;

/**
 * Usage: java ChainProbe.java <key.p12> <served-chain.pem> <truststore.p12> <password>
 * Builds an in-memory server key store from the private key in key.p12 (alias "leaf") and
 * exactly the certificates in served-chain.pem, in file order. Starts an HTTPS server on
 * 127.0.0.1, connects once with a client that trusts only truststore.p12, prints one line.
 * Optional 5th and 6th arguments: a port and a DER file. When given, a plain HTTP server on
 * 127.0.0.1:<port> serves that file at /inter.cer, standing in for a CA's AIA download URL.
 */
public final class ChainProbe {
  private static KeyStore load(String path, char[] password) throws Exception {
    KeyStore store = KeyStore.getInstance("PKCS12");
    try (InputStream in = new FileInputStream(path)) {
      store.load(in, password);
    }
    return store;
  }

  public static void main(String[] args) throws Exception {
    char[] password = args[3].toCharArray();
    KeyStore keySource = load(args[0], password);
    PrivateKey key = (PrivateKey) keySource.getKey("leaf", password);
    Certificate[] served;
    try (InputStream in = new FileInputStream(args[1])) {
      served = CertificateFactory.getInstance("X.509").generateCertificates(in).toArray(new Certificate[0]);
    }
    KeyStore serverStore = KeyStore.getInstance("PKCS12");
    serverStore.load(null, null);
    serverStore.setKeyEntry("leaf", key, password, served);
    KeyManagerFactory kmf = KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm());
    kmf.init(serverStore, password);
    SSLContext serverContext = SSLContext.getInstance("TLS");
    serverContext.init(kmf.getKeyManagers(), null, null);

    HttpsServer server = HttpsServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
    server.setHttpsConfigurator(new HttpsConfigurator(serverContext));
    server.createContext("/", exchange -> {
      byte[] body = "ok\n".getBytes(StandardCharsets.US_ASCII);
      exchange.sendResponseHeaders(200, body.length);
      exchange.getResponseBody().write(body);
      exchange.close();
    });
    server.start();
    com.sun.net.httpserver.HttpServer aia = null;
    if (args.length >= 6) {
      byte[] der = java.nio.file.Files.readAllBytes(java.nio.file.Path.of(args[5]));
      aia = com.sun.net.httpserver.HttpServer.create(new InetSocketAddress("127.0.0.1", Integer.parseInt(args[4])), 0);
      aia.createContext("/inter.cer", exchange -> {
        exchange.getResponseHeaders().add("Content-Type", "application/pkix-cert");
        exchange.sendResponseHeaders(200, der.length);
        exchange.getResponseBody().write(der);
        exchange.close();
      });
      aia.start();
    }
    try {
      TrustManagerFactory tmf = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
      tmf.init(load(args[2], password));
      SSLContext clientContext = SSLContext.getInstance("TLS");
      clientContext.init(null, tmf.getTrustManagers(), null);
      HttpClient client = HttpClient.newBuilder().sslContext(clientContext)
          .connectTimeout(Duration.ofSeconds(5)).build();
      URI uri = URI.create("https://localhost:" + server.getAddress().getPort() + "/");
      try {
        HttpResponse<String> response = client.send(HttpRequest.newBuilder(uri).build(),
            HttpResponse.BodyHandlers.ofString());
        System.out.println("served_chain_length=" + served.length + " result=OK status=" + response.statusCode());
      } catch (SSLHandshakeException e) {
        String reason = e.getMessage() == null ? "" : e.getMessage();
        String kind = reason.contains("PKIX path building failed") ? "PKIX_PATH_BUILDING_FAILED" : "HANDSHAKE_FAILED";
        System.out.println("served_chain_length=" + served.length + " result=" + kind);
      }
    } finally {
      server.stop(0);
      if (aia != null) {
        aia.stop(0);
      }
    }
  }
}
