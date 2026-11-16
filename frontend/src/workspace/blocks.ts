// Helpers for the feature blocks the annotator marks inside the SERP iframe.
// The annotator adds "aqlqa-sf-testing" in DevTools; accepting swaps it for "aqlqa-sf-accepted".

const TESTING = "aqlqa-sf-testing";
const ACCEPTED = "aqlqa-sf-accepted";
const INDEX_ATTR = "aqlqa-sf-index";
const STYLE_ID = "fb-annotation-styles";
// the backend numbers every element of the snapshot; the save sends this number
const NODE_ATTR = "aqlqa-node";
// the same attribute the backend writes into the saved snapshot, shown here right away
const TYPE_ATTR = "aqlqa-sf-type";

export type MarkResult = { element: Element; node: number } | { error: string };

export function findMarkedElement(doc: Document): MarkResult {
  const marked = doc.querySelectorAll(`.${TESTING}`);
  if (marked.length === 0) return { error: "Mark a block in DevTools first." };
  if (marked.length > 1) return { error: "Mark only one block at a time." };
  const element = marked[0];
  if (element.classList.contains(ACCEPTED)) return { error: "This block is already accepted." };
  // only elements from the archived page carry a number; one the browser added
  // itself (such as <tbody>) doesn't exist in the snapshot, so it can't be saved
  const node = Number(element.getAttribute(NODE_ATTR));
  if (!Number.isInteger(node) || node < 1) {
    return { error: "This element was added by the browser. Mark its parent element instead." };
  }
  return { element, node };
}

export function markAccepted(element: Element, index: number, featureType: string): void {
  element.classList.remove(TESTING);
  element.classList.add(ACCEPTED);
  element.setAttribute(INDEX_ATTR, String(index));
  element.setAttribute(TYPE_ATTR, featureType);
}

export function unmarkAccepted(doc: Document, index: number): void {
  const element = doc.querySelector(`[${INDEX_ATTR}="${index}"]`);
  if (!element) return;
  element.classList.remove(ACCEPTED);
  element.removeAttribute(INDEX_ATTR);
  element.removeAttribute(TYPE_ATTR);
  if (element.classList.length === 0) element.removeAttribute("class");
}

// the editor: find a saved feature's element by its aqlqa-node number
export function elementByNode(doc: Document, node: number): Element | null {
  return doc.querySelector(`[${NODE_ATTR}="${node}"]`);
}

// the editor: change an accepted block's type in the page
export function setBlockType(doc: Document, index: number, featureType: string): void {
  doc.querySelector(`[${INDEX_ATTR}="${index}"]`)?.setAttribute(TYPE_ATTR, featureType);
}

// what gets saved as the feature's content: the block as the SERP had it, without our marks
export function blockContent(element: Element): string {
  const copy = element.cloneNode(true) as Element;
  for (const el of [copy, ...copy.querySelectorAll(`.${TESTING}, .${ACCEPTED}, [${INDEX_ATTR}]`)]) {
    el.classList.remove(TESTING, ACCEPTED);
    el.removeAttribute(INDEX_ATTR);
    if (el.classList.length === 0) el.removeAttribute("class");
  }
  return copy.outerHTML;
}

export function injectOutlineStyles(doc: Document): void {
  if (doc.getElementById(STYLE_ID)) return;
  const style = doc.createElement("style");
  style.id = STYLE_ID;
  // the old app's highlights: a see-through fill over the whole block plus an outline,
  // orange while marking, green (and slightly dimmed) once accepted
  style.textContent =
    `.${TESTING} { outline: 3px solid #FFA500 !important; outline-offset: 2px;` +
    ` background-color: rgba(255, 165, 0, 0.1) !important; transition: all 0.3s ease; }\n` +
    `.${ACCEPTED} { outline: 2px solid #4CAF50 !important; outline-offset: 2px;` +
    ` background-color: rgba(76, 175, 80, 0.1) !important; opacity: 0.7; transition: all 0.3s ease; }\n` +
    // a small label with the type at the start of each accepted block
    `.${ACCEPTED}[${TYPE_ATTR}]::before { content: attr(${TYPE_ATTR}); display: inline-block;` +
    ` margin: 0 6px 2px 0; padding: 0 5px; border-radius: 3px; background: #4CAF50; color: #fff;` +
    ` font: 500 11px/1.6 -apple-system, BlinkMacSystemFont, sans-serif; }`;
  doc.head.appendChild(style);
}
