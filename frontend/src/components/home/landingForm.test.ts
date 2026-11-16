import { expect, test } from "vitest";
import { countMessage, missingFields } from "./landingForm";

test("count: leads with what's left, with thousands separators", () => {
  expect(countMessage({ total: 38540, annotated: 37 })).toBe("38,503 left to annotate, of 38,540 SERPs.");
});

test("count: says when nothing matches", () => {
  expect(countMessage({ total: 0, annotated: 0 })).toBe("No SERPs match these choices.");
});

test("count: says when everything is annotated, singular for one", () => {
  expect(countMessage({ total: 1, annotated: 1 })).toBe("Nothing left to annotate (1 SERP, all annotated).");
});

test("reports empty and whitespace-only fields", () => {
  expect(missingFields({ provider: "Google", language: "", year: "2012", createdBy: "  " }))
    .toEqual(["language", "createdBy"]);
});

test("reports nothing when all fields are filled", () => {
  expect(missingFields({ provider: "Google", language: "English", year: "2012", createdBy: "hurjiang" })).toEqual([]);
});
