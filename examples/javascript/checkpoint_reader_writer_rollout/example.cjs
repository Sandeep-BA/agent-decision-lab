// Author: Sandeep Belgavi. Offline synthetic fixture.
const model=require('../daily-20261124-models.cjs');
console.log(JSON.stringify(model.rollout(require('./fixture.json')),null,2));
