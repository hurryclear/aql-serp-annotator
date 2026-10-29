export type ShortcutAction = "skip" | "accept" | "save" | "noBlocks";

const KEYS: Record<string, ShortcutAction> = { "1": "skip", "2": "accept", "3": "save", "4": "noBlocks" };

// The event may come from inside the SERP iframe, where `instanceof HTMLElement`
// is false (another window's classes), so check the tag name instead.
function isTyping(target: EventTarget | null): boolean {
  if (!target || !("tagName" in target)) return false;
  const element = target as Element;
  if (["INPUT", "TEXTAREA", "SELECT"].includes(element.tagName)) return true;
  return element.closest('[contenteditable=""], [contenteditable="true"]') !== null;
}

export function shortcutFor(event: KeyboardEvent): ShortcutAction | null {
  if (event.ctrlKey || event.metaKey || event.altKey) return null;
  if (isTyping(event.target)) return null;
  return KEYS[event.key] ?? null;
}
