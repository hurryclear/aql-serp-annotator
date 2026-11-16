// Matches in the order a person expects: options that start with the typed text,
// then options with a word that starts with it ("chin" → "Simplified Chinese"),
// then any other option containing it. So "eng" puts English above Bengali.
export function rankOptions(options: string[], typed: string): string[] {
  const query = typed.trim().toLowerCase();
  if (!query) return options;
  const rank = (option: string) => {
    const text = option.toLowerCase();
    if (text.startsWith(query)) return 0;
    if (text.split(/\s+/).some((word) => word.startsWith(query))) return 1;
    return text.includes(query) ? 2 : -1;
  };
  return options
    .map((option) => ({ option, rank: rank(option) }))
    .filter(({ rank }) => rank >= 0)
    .sort((a, b) => a.rank - b.rank) // stable: same rank keeps the list's order
    .map(({ option }) => option);
}
