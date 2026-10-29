import { expect, test } from "vitest";
import { shortcutFor } from "./shortcuts";

function key(k: string, target: Element = document.body, mods: KeyboardEventInit = {}): KeyboardEvent {
  const event = new KeyboardEvent("keydown", { key: k, bubbles: true, ...mods });
  Object.defineProperty(event, "target", { value: target });
  return event;
}

test("maps 1-4 to actions", () => {
  expect(shortcutFor(key("1"))).toBe("skip");
  expect(shortcutFor(key("2"))).toBe("accept");
  expect(shortcutFor(key("3"))).toBe("save");
  expect(shortcutFor(key("4"))).toBe("noBlocks");
});

test("ignores keys typed in a text field", () => {
  expect(shortcutFor(key("1", document.createElement("input")))).toBeNull();
  expect(shortcutFor(key("1", document.createElement("textarea")))).toBeNull();
});

test("ignores keys typed in an editable element", () => {
  const div = document.createElement("div");
  div.setAttribute("contenteditable", "true");
  expect(shortcutFor(key("2", div))).toBeNull();
});

test("ignores keys with modifiers", () => {
  expect(shortcutFor(key("2", document.body, { metaKey: true }))).toBeNull();
  expect(shortcutFor(key("3", document.body, { ctrlKey: true }))).toBeNull();
});

test("ignores other keys", () => {
  expect(shortcutFor(key("5"))).toBeNull();
});
