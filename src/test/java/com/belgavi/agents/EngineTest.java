// Author: Sandeep Belgavi
package com.belgavi.agents;

import org.junit.jupiter.api.*;
import java.util.*;
import java.util.stream.Stream;
import static org.junit.jupiter.api.Assertions.*;

class EngineTest {
    Engine.Decision good(String choice) { return new Engine.Decision(choice,Map.of("proceed",choice.equals("proceed")?0.95:0.025,"review",choice.equals("review")?0.95:0.025,"block",choice.equals("block")?0.95:0.025),0.925,"fixture"); }
    @TestFactory Stream<DynamicTest> everyRecipe() throws Exception {
        var recipes=Main.recipes(); assertEquals(100,recipes.size()); assertEquals(100,recipes.stream().map(Engine.Recipe::id).distinct().count());
        return recipes.stream().flatMap(r -> {
            Map<String,Object> state=new LinkedHashMap<>(); r.requiredEvidence().forEach(k->state.put(k,"Synthetic evidence")); state.put("secret","must-not-reach-model");
            var engine=new Engine(); var tests=new ArrayList<DynamicTest>();
            tests.add(DynamicTest.dynamicTest(r.id()+": happy path and minimization",()->{
                var result=engine.run(r,new Engine.Context(r.scope(),1,state,true),(recipe,minimized)->{ assertFalse(minimized.containsKey("secret")); return good("proceed"); });
                assertEquals("RECOMMENDATION_READY",result.status()); assertEquals(1,result.calls()); assertEquals("audit:RECOMMENDATION_READY",result.trace().get(result.trace().size()-1));
            }));
            tests.add(DynamicTest.dynamicTest(r.id()+": wrong scope",()-> assertEquals("DENIED",engine.run(r,new Engine.Context("wrong",1,state,true),(a,b)->{fail("Model must not run");return null;}).status())));
            tests.add(DynamicTest.dynamicTest(r.id()+": budget",()-> assertEquals("BUDGET_EXHAUSTED",engine.run(r,new Engine.Context(r.scope(),0,state,true),(a,b)->{fail("Model must not run");return null;}).status())));
            tests.add(DynamicTest.dynamicTest(r.id()+": missing evidence",()-> assertEquals("MISSING_EVIDENCE",engine.run(r,new Engine.Context(r.scope(),1,Map.of(),true),(a,b)->{fail("Model must not run");return null;}).status())));
            tests.add(DynamicTest.dynamicTest(r.id()+": approval",()-> assertEquals("AWAITING_APPROVAL",engine.run(r,new Engine.Context(r.scope(),1,state,false),(a,b)->good("proceed")).status())));
            tests.add(DynamicTest.dynamicTest(r.id()+": review",()-> assertEquals("NEEDS_REVIEW",engine.run(r,new Engine.Context(r.scope(),1,state,true),(a,b)->good("review")).status())));
            tests.add(DynamicTest.dynamicTest(r.id()+": blocked",()-> assertEquals("BLOCKED",engine.run(r,new Engine.Context(r.scope(),1,state,true),(a,b)->good("block")).status())));
            tests.add(DynamicTest.dynamicTest(r.id()+": invalid output",()-> assertEquals("INVALID_OUTPUT",engine.run(r,new Engine.Context(r.scope(),1,state,true),(a,b)->new Engine.Decision("execute-shell",Map.of("execute-shell",1.0),1,"fixture")).status())));
            tests.add(DynamicTest.dynamicTest(r.id()+": outage",()-> assertEquals("PROVIDER_UNAVAILABLE",engine.run(r,new Engine.Context(r.scope(),1,state,true),(a,b)->{throw new Exception("secret");}).status())));
            tests.add(DynamicTest.dynamicTest(r.id()+": uncertainty",()-> assertEquals("NEEDS_REVIEW",engine.run(r,new Engine.Context(r.scope(),1,state,true),(a,b)->new Engine.Decision("proceed",Map.of("proceed",0.4,"review",0.3,"block",0.3),0.1,"fixture")).status())));
            return tests.stream();
        });
    }
    @Test void validatesProviderContract() throws Exception {
        var recipe=Main.recipes().get(0);
        var client=new JevClient("jev-1.13.0",body->{
            var request=JevClient.JSON.readTree(body); assertEquals("choice",request.path("questions").path("decision").path("type").asText()); assertEquals("jev-1.13.0",request.path("model").asText());
            return "{\"model\":\"jev-1.13.0\",\"answers\":{\"decision\":{\"type\":\"choice\",\"choice\":\"proceed\",\"probabilities\":{\"proceed\":0.95,\"review\":0.04,\"block\":0.01},\"confidence\":0.925}}}";
        });
        assertTrue(Engine.valid(recipe,client.decide(recipe,Map.of("ticket","fixture"))));
        assertThrows(Exception.class,()->new JevClient("jev-1.13.0",body->"{}").decide(recipe,Map.of()));
        assertFalse(Engine.valid(recipe,new Engine.Decision("proceed",Map.of("proceed",0.1,"review",0.8,"block",0.1),0.7,"fixture")));
    }
}
