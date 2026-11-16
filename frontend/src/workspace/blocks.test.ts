import { expect, test } from "vitest";
import { blockContent, findMarkedElement, injectOutlineStyles, markAccepted, unmarkAccepted } from "./blocks";

function docWith(body: string): Document {
  const doc = document.implementation.createHTMLDocument();
  doc.body.innerHTML = body;
  return doc;
}

test("finds the single marked element and its node number", () => {
  const doc = docWith('<div id="a" class="aqlqa-sf-testing" aqlqa-node="7">x</div><div>y</div>');
  expect(findMarkedElement(doc)).toEqual({ element: doc.getElementById("a"), node: 7 });
});

test("refuses an element the browser added, which has no node number", () => {
  const doc = docWith('<table aqlqa-node="3"><tbody class="aqlqa-sf-testing"><tr><td>x</td></tr></tbody></table>');
  expect(findMarkedElement(doc)).toEqual({ error: "This element was added by the browser. Mark its parent element instead." });
});

test("refuses when nothing is marked", () => {
  expect(findMarkedElement(docWith("<div>x</div>"))).toEqual({ error: "Mark a block in DevTools first." });
});

test("refuses two marked elements", () => {
  const doc = docWith('<div class="aqlqa-sf-testing">x</div><div class="aqlqa-sf-testing">y</div>');
  expect(findMarkedElement(doc)).toEqual({ error: "Mark only one block at a time." });
});

test("refuses an already accepted element", () => {
  const doc = docWith('<div class="aqlqa-sf-accepted aqlqa-sf-testing" aqlqa-sf-index="1">x</div>');
  expect(findMarkedElement(doc)).toEqual({ error: "This block is already accepted." });
});

test("blockContent strips annotation marks", () => {
  const doc = docWith('<div id="a" class="kp aqlqa-sf-accepted" aqlqa-sf-index="1"><b>x</b></div>');
  expect(blockContent(doc.getElementById("a")!)).toBe('<div id="a" class="kp"><b>x</b></div>');
});

test("blockContent drops an emptied class attribute", () => {
  const doc = docWith('<div class="aqlqa-sf-testing">y</div>');
  expect(blockContent(doc.querySelector("div")!)).toBe("<div>y</div>");
});

test("blockContent leaves the page itself untouched", () => {
  const doc = docWith('<div class="aqlqa-sf-accepted" aqlqa-sf-index="2">y</div>');
  blockContent(doc.querySelector("div")!);
  expect(doc.querySelector(".aqlqa-sf-accepted")?.getAttribute("aqlqa-sf-index")).toBe("2");
});

test("markAccepted then unmarkAccepted restores the element", () => {
  const doc = docWith('<div class="kp aqlqa-sf-testing">x</div>');
  const el = doc.querySelector("div")!;
  markAccepted(el, 3, "knowledge_panel");
  expect(el.className).toBe("kp aqlqa-sf-accepted");
  expect(el.getAttribute("aqlqa-sf-index")).toBe("3");
  expect(el.getAttribute("aqlqa-sf-type")).toBe("knowledge_panel");
  unmarkAccepted(doc, 3);
  expect(el.className).toBe("kp");
  expect(el.hasAttribute("aqlqa-sf-index")).toBe(false);
  expect(el.hasAttribute("aqlqa-sf-type")).toBe(false);
});

test("injectOutlineStyles is idempotent", () => {
  const doc = docWith("<div>x</div>");
  injectOutlineStyles(doc);
  injectOutlineStyles(doc);
  expect(doc.querySelectorAll("#fb-annotation-styles")).toHaveLength(1);
});
