// Author: Sandeep Belgavi. Validate expected fixture outcome.
const assert=require('node:assert/strict');
const model=require('../daily-20261124-models.cjs');
const r=model.judge(require('./fixture.json'));assert.equal(r.metrics.singleA,42);assert.equal(r.metrics.flips,37);assert.equal(r.metrics.consistentA,12);assert.equal(r.metrics.consistentB,11);assert.equal(model.signP(10,0),2/1024);assert.equal(r.rows.length,60);
console.log('Expected outcomes passed');
