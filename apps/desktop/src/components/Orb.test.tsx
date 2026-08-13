import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Orb } from "@/components/Orb";
import { ORB_STATES, ORB_STATE_META } from "@/state/orbState";

describe("Orb", () => {
  it("renders every legal state with the correct data attribute", () => {
    for (const state of ORB_STATES) {
      const { container, unmount } = render(<Orb state={state} />);
      expect(container.querySelector("[data-orb-state]")).toHaveAttribute("data-orb-state", state);
      unmount();
    }
  });

  it("renders the state label from metadata", () => {
    render(<Orb state="THINKING" />);
    expect(screen.getByText(ORB_STATE_META.THINKING.label)).toBeInTheDocument();
  });

  it("exposes a polite status role with a descriptive aria-label", () => {
    render(<Orb state="RESPONDING" />);
    const region = screen.getByRole("status");
    expect(region).toHaveAttribute("aria-label", `Agent status: ${ORB_STATE_META.RESPONDING.label}`);
  });

  it("marks the ERROR state with the error modifier class", () => {
    const { container } = render(<Orb state="ERROR" />);
    expect(container.querySelector(".orb-core--error")).not.toBeNull();
  });
});
