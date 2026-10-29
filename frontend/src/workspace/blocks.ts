// Helpers for the feature blocks the annotator marks inside the SERP iframe.
// The annotator adds "fb-testing" in DevTools; accepting swaps it for "fb-accepted".

const TESTING = "fb-testing";
const ACCEPTED = "fb-accepted";
const INDEX_ATTR = "data-fb-index";
const STYLE_ID = "fb-annotation-styles";

export type MarkResult = { element: Element } | { error: string };

export function findMarkedElement(doc: Document): MarkResult {
  const marked = doc.querySelectorAll(`.${TESTING}`);
  if (marked.length === 0) return { error: "Mark a block in DevTools first." };
  if (marked.length > 1) return { error: "Mark only one block at a time." };
  const element = marked[0];
  if (element.classList.contains(ACCEPTED)) return { error: "This block is already accepted." };
  return { element };
}

export function markAccepted(element: Element, index: number): void {
  element.classList.remove(TESTING);
  element.classList.add(ACCEPTED);
  element.setAttribute(INDEX_ATTR, String(index));
}

export function unmarkAccepted(doc: Document, index: number): void {
  const element = doc.querySelector(`[${INDEX_ATTR}="${index}"]`);
  if (!element) return;
  element.classList.remove(ACCEPTED);
  element.removeAttribute(INDEX_ATTR);
  if (element.classList.length === 0) element.removeAttribute("class");
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
  style.textContent =
    `.${TESTING} { outline: 2px solid #EF9F27 !important; outline-offset: 2px; }\n` +
    `.${ACCEPTED} { outline: 2px dashed #7F77DD !important; outline-offset: 2px; }`;
  doc.head.appendChild(style);
}
