import { expect, test } from "vitest";
import { missingFields } from "./landingForm";

test("reports empty and whitespace-only fields", () => {
  expect(missingFields({ provider: "Google", language: "", year: "2012", createdBy: "  " }))
    .toEqual(["language", "createdBy"]);
});

test("reports nothing when all fields are filled", () => {
  expect(missingFields({ provider: "Google", language: "English", year: "2012", createdBy: "hurjiang" })).toEqual([]);
});
