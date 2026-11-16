import type { SerpCount } from "../../types/workspace";

// the line above the Start button, once the backend has counted the SERPs for these choices
// leads with what's left, since that's what Start hands out; the total comes second
export function countMessage({ total, annotated }: SerpCount): string {
  // not "try a different year": the year may be the one thing not chosen yet
  if (total === 0) return "No SERPs match these choices.";
  if (annotated >= total) return `Nothing left to annotate (${serps(total)}, all annotated).`;
  const left = total - annotated;
  return `${number(left)} left to annotate, of ${serps(total)}.`;
}

// a fixed locale, so 38540 is always "38,540", whatever the browser's language
function number(n: number): string {
  return n.toLocaleString("en-US");
}

function serps(n: number): string {
  return `${number(n)} ${n === 1 ? "SERP" : "SERPs"}`;
}

export type CartForm = {
  provider: string;
  language: string;
  year: string;
  createdBy: string;
};

// fields the annotator still has to fill in; whitespace alone doesn't count
export function missingFields(form: CartForm): (keyof CartForm)[] {
  return (Object.keys(form) as (keyof CartForm)[]).filter((field) => form[field].trim() === "");
}
