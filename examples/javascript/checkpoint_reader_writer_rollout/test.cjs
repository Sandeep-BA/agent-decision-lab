// Author: Sandeep Belgavi. Validate expected fixture outcome.
const assert=require('node:assert/strict');
const model=require('../daily-20261124-models.cjs');
const p=require('./fixture.json');assert.equal(model.rollout(p).metrics.rejected,3);assert.equal(model.rollout({...p,strategy:'readers_first'}).metrics.rejected,0);assert.equal(model.rollout({...p,route:true}).metrics.rejected,0);assert(model.rollout({...p,strategy:'rollback',route:true}).metrics.rejected>0);
console.log('Expected outcomes passed');
