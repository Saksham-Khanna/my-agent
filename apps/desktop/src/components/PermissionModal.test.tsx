import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PermissionModal } from "@/components/PermissionModal";
import type { PermissionRequest } from "@/components/PermissionModal";

const request: PermissionRequest = {
  request_id: "req-1",
  title: "Run shell command",
  description: "Run `dir` in the working directory.",
  riskLevel: "high",
};

describe("PermissionModal", () => {
  it("renders nothing when there is no request", () => {
    const { container } = render(<PermissionModal request={null} onAllow={vi.fn()} onDeny={vi.fn()} />);
    expect(container.querySelector("[role='alertdialog']")).toBeNull();
  });

  it("shows risk level, title, and description", () => {
    render(<PermissionModal request={request} onAllow={vi.fn()} onDeny={vi.fn()} />);
    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
    expect(screen.getByText("high risk")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Run shell command" })).toBeInTheDocument();
    expect(screen.getByText(/`dir` in the working directory/)).toBeInTheDocument();
  });

  it("auto-focuses the Deny button on open (safety-first)", async () => {
    render(<PermissionModal request={request} onAllow={vi.fn()} onDeny={vi.fn()} />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Deny" })).toHaveFocus());
  });

  it("calls onAllow when Allow is clicked", async () => {
    const onAllow = vi.fn();
    render(<PermissionModal request={request} onAllow={onAllow} onDeny={vi.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: "Allow" }));
    expect(onAllow).toHaveBeenCalledTimes(1);
  });

  it("calls onDeny when Deny is clicked", async () => {
    const onDeny = vi.fn();
    render(<PermissionModal request={request} onAllow={vi.fn()} onDeny={onDeny} />);
    await userEvent.click(screen.getByRole("button", { name: "Deny" }));
    expect(onDeny).toHaveBeenCalledTimes(1);
  });

  it("denies on Escape", async () => {
    const onDeny = vi.fn();
    render(<PermissionModal request={request} onAllow={vi.fn()} onDeny={onDeny} />);
    await userEvent.keyboard("{Escape}");
    expect(onDeny).toHaveBeenCalledTimes(1);
  });

  it("traps focus so Tab on the last button wraps to the first", async () => {
    render(<PermissionModal request={request} onAllow={vi.fn()} onDeny={vi.fn()} />);
    const allowButton = screen.getByRole("button", { name: "Allow" });
    allowButton.focus();
    fireEvent.keyDown(allowButton, { key: "Tab" });
    expect(screen.getByRole("button", { name: "Deny" })).toHaveFocus();
  });

  it("does not attach the Escape handler when closed", async () => {
    const onDeny = vi.fn();
    render(<PermissionModal request={null} onAllow={vi.fn()} onDeny={onDeny} />);
    await userEvent.keyboard("{Escape}");
    expect(onDeny).not.toHaveBeenCalled();
  });
});
