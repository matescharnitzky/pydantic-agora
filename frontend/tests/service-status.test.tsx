import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { ServiceStatus } from "@/components/service-status";

it.each([
  [true, "API and database are ready"],
  [false, "API is unavailable"],
] as const)("announces service readiness (%s)", (ready, message) => {
  render(<ServiceStatus ready={ready} />);
  expect(screen.getByRole("status")).toHaveTextContent(message);
});
