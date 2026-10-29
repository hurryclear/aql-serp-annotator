import { expect, test } from "vitest";
import { blockContent, findMarkedElement, injectOutlineStyles, markAccepted, unmarkAccepted } from "./blocks";

function docWith(body: string): Document {
  const doc = document.implementation.createHTMLDocument();
  doc.body.innerHTML = body;
  return doc;
}

test("finds the single marked element", () => {
  const doc = docWith('<div id="a" class="fb-testing">x</div><div>y</div>');
  expect(findMarkedElement(doc)).toEqual({ element: doc.getElementById("a") });
});

test("refuses when nothing is marked", () => {
  expect(findMarkedElement(docWith("<div>x</div>"))).toEqual({ error: "Mark a block in DevTools first." });
});

test("refuses two marked elements", () => {
  const doc = docWith('<div class="fb-testing">x</div><div class="fb-testing">y</div>');
  expect(findMarkedElement(doc)).toEqual({ error: "Mark only one block at a time." });
});

test("refuses an already accepted element", () => {
  const doc = docWith('<div class="fb-accepted fb-testing" data-fb-index="1">x</div>');
  expect(findMarkedElement(doc)).toEqual({ error: "This block is already accepted." });
});

test("blockContent strips annotation marks", () => {
  const doc = docWith('<div id="a" class="kp fb-accepted" data-fb-index="1"><b>x</b></div>');
  expect(blockContent(doc.getElementById("a")!)).toBe('<div id="a" class="kp"><b>x</b></div>');
});

test("blockContent drops an emptied class attribute", () => {
  const doc = docWith('<div class="fb-testing">y</div>');
  expect(blockContent(doc.querySelector("div")!)).toBe("<div>y</div>");
});

test("blockContent leaves the page itself untouched", () => {
  const doc = docWith('<div class="fb-accepted" data-fb-index="2">y</div>');
  blockContent(doc.querySelector("div")!);
  expect(doc.querySelector(".fb-accepted")?.getAttribute("data-fb-index")).toBe("2");
});

test("markAccepted then unmarkAccepted restores the element", () => {
  const doc = docWith('<div class="kp fb-testing">x</div>');
  const el = doc.querySelector("div")!;
  markAccepted(el, 3);
  expect(el.className).toBe("kp fb-accepted");
  expect(el.getAttribute("data-fb-index")).toBe("3");
  unmarkAccepted(doc, 3);
  expect(el.className).toBe("kp");
  expect(el.hasAttribute("data-fb-index")).toBe(false);
});

test("injectOutlineStyles is idempotent", () => {
  const doc = docWith("<div>x</div>");
  injectOutlineStyles(doc);
  injectOutlineStyles(doc);
  expect(doc.querySelectorAll("#fb-annotation-styles")).toHaveLength(1);
});
