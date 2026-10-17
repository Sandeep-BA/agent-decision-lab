// Author: Sandeep Belgavi
package com.belgavi.agents;

import com.fasterxml.jackson.databind.*;
import java.net.*;
import java.net.http.*;
import java.time.Duration;
import java.util.*;

/** Uses the documented TypeSafe HTTP API; not an official TypeSafe Java SDK. */
public final class JevClient implements Engine.Model {
    static final ObjectMapper JSON = new ObjectMapper();
    public interface Transport { String post(String body) throws Exception; }
    private final Transport transport; private final String model;
    public JevClient(String model,Transport transport) {
        if (model == null || !model.matches("jev-[a-zA-Z0-9.-]{1,64}")) throw new IllegalArgumentException("Choose a documented Jev model ID");
        this.model=model; this.transport=transport;
    }
    public static JevClient live(String model,String key) {
        if (key == null || key.isBlank() || key.contains("\n") || key.contains("\r")) throw new IllegalArgumentException("TYPESAFE_API_KEY required");
        HttpClient http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).followRedirects(HttpClient.Redirect.NEVER).build();
        return new JevClient(model, body -> {
            if (body.getBytes(java.nio.charset.StandardCharsets.UTF_8).length > 65536) throw new IllegalArgumentException("Input exceeds 64 KiB");
            var request = HttpRequest.newBuilder(URI.create("https://api.typesafe.ai/v1/systemone"))
                .timeout(Duration.ofSeconds(15)).header("Authorization","Bearer "+key).header("Content-Type","application/json")
                .POST(HttpRequest.BodyPublishers.ofString(body)).build();
            var pending = http.sendAsync(request, info -> new LimitedBody());
            HttpResponse<byte[]> response;
            try { response = pending.get(15, java.util.concurrent.TimeUnit.SECONDS); }
            catch (java.util.concurrent.TimeoutException error) { pending.cancel(true); throw new IllegalStateException("Provider deadline exceeded"); }
            if (response.statusCode()!=200) throw new IllegalStateException("Provider HTTP failure");
            return new String(response.body(),java.nio.charset.StandardCharsets.UTF_8);
        });
    }
    static final class LimitedBody implements HttpResponse.BodySubscriber<byte[]> {
        final java.util.concurrent.CompletableFuture<byte[]> result = new java.util.concurrent.CompletableFuture<>();
        final java.io.ByteArrayOutputStream bytes = new java.io.ByteArrayOutputStream();
        java.util.concurrent.Flow.Subscription subscription;
        public java.util.concurrent.CompletionStage<byte[]> getBody() { return result; }
        public void onSubscribe(java.util.concurrent.Flow.Subscription s) { subscription=s; s.request(1); }
        public void onNext(List<java.nio.ByteBuffer> buffers) {
            for(var buffer:buffers) {
                if(bytes.size()+buffer.remaining()>65536) { subscription.cancel(); result.completeExceptionally(new IllegalStateException("Provider response too large")); return; }
                byte[] chunk=new byte[buffer.remaining()]; buffer.get(chunk); bytes.writeBytes(chunk);
            }
            subscription.request(1);
        }
        public void onError(Throwable error) { result.completeExceptionally(error); }
        public void onComplete() { result.complete(bytes.toByteArray()); }
    }
    @Override public Engine.Decision decide(Engine.Recipe recipe,Map<String,Object> state) throws Exception {
        String body=JSON.writeValueAsString(Map.of("model",model,"state",state,"questions",Map.of("decision",Map.of("type","choice","instructions",recipe.task(),"criteria",recipe.choices()))));
        JsonNode root=JSON.readTree(transport.post(body)); JsonNode answer=root.path("answers").path("decision");
        if (!answer.path("type").asText().equals("choice") || !answer.path("confidence").isNumber() || !answer.path("probabilities").isObject()) throw new IllegalStateException("Invalid provider schema");
        Map<String,Double> probabilities=new LinkedHashMap<>();
        var fields=answer.path("probabilities").fields();
        while(fields.hasNext()) { var field=fields.next(); if(!field.getValue().isNumber()) throw new IllegalStateException("Invalid probability"); probabilities.put(field.getKey(),field.getValue().doubleValue()); }
        return new Engine.Decision(answer.path("choice").asText(),probabilities,answer.path("confidence").doubleValue(),root.path("model").asText());
    }
}
