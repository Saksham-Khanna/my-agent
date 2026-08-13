import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ModeDock } from "@/components/ModeDock";
import { AGENT_MODES } from "@/state/types";
import type { AgentMode } from "@/state/types";

function renderDock() {
  const onSelect = vi.fn<(mode: AgentMode) => void>();
  render(<ModeDock activeMode="talk" onSelect={onSelect} />);
  return onSelect;
}

describe("ModeDock", () => {
  it("renders all six modes as tabs with the active one selected", () => {
    renderDock();
    const tabs = screen.getAllByRole("tab");
    expect(tabs).toHaveLength(AGENT_MODES.length);

    const talkTab = screen.getByRole("tab", { name: "Talk" });
    expect(talkTab).toHaveAttribute("aria-selected", "true");
    expect(talkTab).toHaveAttribute("tabindex", "0");
    expect(screen.getByRole("tab", { name: "Vision" })).toHaveAttribute("aria-selected", "false");
  });

  it("calls onSelect when a mode button is clicked", () => {
    const onSelect = renderDock();
    fireEvent.click(screen.getByRole("tab", { name: "Actions" }));
    expect(onSelect).toHaveBeenCalledWith("actions");
  });

  it("moves to the next mode on ArrowRight", () => {
    const onSelect = renderDock();
    fireEvent.keyDown(screen.getByRole("tablist"), { key: "ArrowRight" });
    expect(onSelect).toHaveBeenCalledWith(AGENT_MODES[1].id);
  });

  it("wraps from the last mode back to the first on ArrowRight", () => {
    const onSelect = vi.fn<(mode: AgentMode) => void>();
    render(<ModeDock activeMode="actions" onSelect={onSelect} />);
    const dock = screen.getByRole("tablist");
    fireEvent.keyDown(dock, { key: "ArrowRight" });
    expect(onSelect).toHaveBeenCalledWith("talk");
  });

  it("moves to the previous mode on ArrowLeft and Home/End jump to ends", () => {
    const onSelect = renderDock();
    const dock = screen.getByRole("tablist");

    fireEvent.keyDown(dock, { key: "ArrowLeft" });
    expect(onSelect).toHaveBeenCalledWith(AGENT_MODES[AGENT_MODES.length - 1].id);

    fireEvent.keyDown(dock, { key: "Home" });
    expect(onSelect).toHaveBeenCalledWith("talk");

    fireEvent.keyDown(dock, { key: "End" });
    expect(onSelect).toHaveBeenCalledWith("actions");
  });
});
