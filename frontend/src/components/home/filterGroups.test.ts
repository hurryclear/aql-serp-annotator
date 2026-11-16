import { describe, expect, it } from "vitest";
import { filterGroups } from "./filterGroups";
import type { AnnotationGroup } from "../../types/editor";

function group(provider: string, year: number): AnnotationGroup {
  return { provider_id: `${provider}-id`, provider, year, annotations: 1, ground_truth: 0 };
}

const groups = [group("google", 2023), group("google", 2024), group("baidu", 2023)];

describe("filterGroups", () => {
  it("keeps every group when nothing is chosen", () => {
    expect(filterGroups(groups, "", "")).toEqual(groups);
  });

  it("keeps every year of a provider, ignoring case", () => {
    expect(filterGroups(groups, "Google", "")).toEqual([groups[0], groups[1]]);
  });

  it("keeps every provider of a year", () => {
    expect(filterGroups(groups, "", "2023")).toEqual([groups[0], groups[2]]);
  });

  it("keeps the one group of a provider and year", () => {
    expect(filterGroups(groups, "Baidu", "2023")).toEqual([groups[2]]);
  });

  it("keeps nothing when no group matches", () => {
    expect(filterGroups(groups, "Bing", "")).toEqual([]);
  });
});
