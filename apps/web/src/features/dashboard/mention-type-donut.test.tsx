import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MentionTypeDonut } from "./mention-type-donut";

describe("MentionTypeDonut", () => {
  it("shows empty state when no responses exist", () => {
    render(<MentionTypeDonut items={[]} totalResponses={0} />);
    expect(screen.getByText(/no responses yet/i)).toBeInTheDocument();
  });

  it("renders the mention percentage", () => {
    render(
      <MentionTypeDonut
        items={[
          { label: "mentioned", count: 3 },
          { label: "not_mentioned", count: 1 },
        ]}
        totalResponses={4}
      />,
    );
    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText(/3 of 4 responses/i)).toBeInTheDocument();
  });

  it("handles the zero-mentions case without crashing", () => {
    render(
      <MentionTypeDonut
        items={[
          { label: "mentioned", count: 0 },
          { label: "not_mentioned", count: 2 },
        ]}
        totalResponses={2}
      />,
    );
    expect(screen.getByText("0%")).toBeInTheDocument();
  });
});
