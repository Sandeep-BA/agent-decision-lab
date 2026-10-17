// Author: Sandeep Belgavi
package com.belgavi.agents;

import java.util.*;

/** Recommendations only. No tool effects, account authentication, or payment processing. */
public final class Engine {
    public record Recipe(String id, String name, String category, String task, String scope,
                         List<String> requiredEvidence, Map<String,String> choices, double threshold) {}
    public record Context(String scope, int remainingCalls, Map<String,Object> state, boolean approval) {}
    public record Decision(String choice, Map<String,Double> probabilities, double confidence, String model) {}
    public record Result(String recipe, String status, String choice, String model, List<String> trace, int calls) {}
    public interface Model { Decision decide(Recipe recipe, Map<String,Object> minimizedState) throws Exception; }
    public Result run(Recipe recipe, Context context, Model model) {
        List<String> trace = new ArrayList<>();
        trace.add("identity-and-scope");
        if (!recipe.scope.equals(context.scope)) return result(recipe,"DENIED","","",trace,0);
        trace.add("budget");
        if (context.remainingCalls < 1) return result(recipe,"BUDGET_EXHAUSTED","","",trace,0);
        trace.add("minimize");
        Map<String,Object> state = new LinkedHashMap<>();
        for (String field : recipe.requiredEvidence) {
            Object value = context.state.get(field);
            if (value == null || !(value instanceof String text) || text.isBlank() || text.length() > 4096)
                return result(recipe,"MISSING_EVIDENCE","","",trace,0);
            state.put(field,value);
        }
        trace.add("model");
        Decision decision;
        try { decision = model.decide(recipe, Collections.unmodifiableMap(state)); }
        catch (Exception e) { return result(recipe,"PROVIDER_UNAVAILABLE","","",trace,1); }
        trace.add("validate");
        if (!valid(recipe,decision)) return result(recipe,"INVALID_OUTPUT","","",trace,1);
        if (decision.choice.equals("block")) return result(recipe,"BLOCKED",decision.choice,decision.model,trace,1);
        if (decision.choice.equals("review") || decision.confidence < recipe.threshold)
            return result(recipe,"NEEDS_REVIEW",decision.choice,decision.model,trace,1);
        trace.add("approval");
        if (!context.approval) return result(recipe,"AWAITING_APPROVAL",decision.choice,decision.model,trace,1);
        // Deliberately stop at a reviewed recommendation, never execute a business effect.
        return result(recipe,"RECOMMENDATION_READY",decision.choice,decision.model,trace,1);
    }
    static Result result(Recipe recipe,String status,String choice,String model,List<String> trace,int calls) {
        trace.add("audit:"+status); return new Result(recipe.id,status,choice,model,List.copyOf(trace),calls);
    }
    public static boolean valid(Recipe recipe,Decision d) {
        if (d == null || d.model == null || d.model.isBlank() || d.probabilities == null || !recipe.choices.keySet().equals(d.probabilities.keySet()) || !recipe.choices.containsKey(d.choice) || !Double.isFinite(d.confidence) || d.confidence < 0 || d.confidence > 1) return false;
        double sum = 0, max = -1;
        for (Double value : d.probabilities.values()) {
            if (value == null || !Double.isFinite(value) || value < 0 || value > 1) return false;
            sum += value; max = Math.max(max,value);
        }
        return Math.abs(sum-1) < 0.0001 && d.probabilities.get(d.choice) >= max - 0.000001;
    }
}
