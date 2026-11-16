import { expect, test } from "vitest";
import { rankOptions } from "./rankOptions";

const LANGUAGES = ["Bengali", "German", "English", "Simplified Chinese", "Traditional Chinese"];

test("options that start with the typed text come first", () => {
  expect(rankOptions(LANGUAGES, "eng")).toEqual(["English", "Bengali"]);
});

test("a word inside the option counts as a start", () => {
  expect(rankOptions(LANGUAGES, "chin")).toEqual(["Simplified Chinese", "Traditional Chinese"]);
});

test("case and surrounding spaces don't matter", () => {
  expect(rankOptions(LANGUAGES, "  GER ")).toEqual(["German"]);
});

test("nothing typed shows every option in its order", () => {
  expect(rankOptions(LANGUAGES, "")).toEqual(LANGUAGES);
});

test("no match gives an empty list", () => {
  expect(rankOptions(LANGUAGES, "xyz")).toEqual([]);
});
