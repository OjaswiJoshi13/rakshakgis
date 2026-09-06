import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

vi.mock("next/navigation", () => {
  const push = vi.fn();
  const replace = vi.fn();
  const back = vi.fn();
  const forward = vi.fn();
  const refresh = vi.fn();
  const prefetch = vi.fn();

  return {
    useRouter: () => ({
      push,
      replace,
      back,
      forward,
      refresh,
      prefetch,
    }),
    usePathname: () => "/",
    useSearchParams: () => new URLSearchParams(),
  };
});
