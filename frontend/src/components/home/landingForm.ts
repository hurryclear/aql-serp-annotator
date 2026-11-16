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
