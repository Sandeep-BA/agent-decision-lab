// Author: Sandeep Belgavi. Prompt template substitution with and without String.replace dollar patterns.
// No dependencies, no network and no model call.

export const TEMPLATE = 'Summarize the case below for the help desk.\n{{case}}\nReply in {{lang}}.';

/** The pattern Gemini CLI 0.68.0 moved away from: one chained replace per placeholder with a string value. */
export function chainedReplace(template, values) {
  let out = template;
  for (const [name, value] of Object.entries(values)) out = out.replace(`{{${name}}}`, value);
  return out;
}

/** Still chained, but each value comes from a function, so dollar patterns are not expanded. */
export function chainedFunction(template, values) {
  let out = template;
  for (const [name, value] of Object.entries(values)) out = out.replace(`{{${name}}}`, () => value);
  return out;
}

/**
 * One pass over the ORIGINAL template. Inserted text is never rescanned, so a value that contains
 * another placeholder stays literal. Unknown placeholders are an error rather than a silent blank.
 */
export function render(template, values) {
  return template.replace(/\{\{(\w+)\}\}/g, (match, name) => {
    if (!Object.prototype.hasOwnProperty.call(values, name)) throw new Error(`no value for ${match}`);
    return String(values[name]);
  });
}

if (import.meta.url === `file://${process.argv[1].replace(/\\/g, '/').replace(/^([A-Za-z]):/, '/$1:')}`) {
  const values = { case: "Customer wrote: refund $' please", lang: 'English' };
  console.log('chained replace:\n' + chainedReplace(TEMPLATE, values));
  console.log('single pass:\n' + render(TEMPLATE, values));
}
