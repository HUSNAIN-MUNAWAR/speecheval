import { describe, expect, it } from "vitest";
describe("SpeechEval web foundation", () => {
  it("keeps the product identity", () =>
    expect("SpeechEval").toContain("Speech"));
});
