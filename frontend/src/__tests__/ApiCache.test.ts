import { describe, it, expect, beforeEach, vi } from "vitest";
import { ApiCache } from "@/lib/api/cache";

describe("ApiCache", () => {
  let cache: ApiCache;

  beforeEach(() => {
    cache = new ApiCache();
    vi.useRealTimers();
  });

  it("stores and retrieves cached items within TTL", () => {
    cache.set("key1", { data: "test" }, 5000);
    expect(cache.get("key1")).toEqual({ data: "test" });
  });

  it("returns null for non-existent keys", () => {
    expect(cache.get("non-existent")).toBeNull();
  });

  it("expires entries when TTL passes", () => {
    vi.useFakeTimers();
    cache.set("expiring-key", { temp: true }, 1000);

    expect(cache.get("expiring-key")).toEqual({ temp: true });

    vi.advanceTimersByTime(1001);

    expect(cache.get("expiring-key")).toBeNull();
  });

  it("does not store entries if ttlMs is non-positive", () => {
    cache.set("zero-ttl", { value: 1 }, 0);
    expect(cache.get("zero-ttl")).toBeNull();

    cache.set("neg-ttl", { value: 2 }, -100);
    expect(cache.get("neg-ttl")).toBeNull();
  });

  it("invalidates specific key", () => {
    cache.set("keyA", "alpha", 5000);
    cache.set("keyB", "beta", 5000);

    cache.invalidate("keyA");
    expect(cache.get("keyA")).toBeNull();
    expect(cache.get("keyB")).toBe("beta");
  });

  it("invalidates keys matching regex pattern", () => {
    cache.set("sites/1/details", { id: 1 }, 5000);
    cache.set("sites/2/details", { id: 2 }, 5000);
    cache.set("villages/1", { id: 1 }, 5000);

    cache.invalidatePattern(/^sites\//);

    expect(cache.get("sites/1/details")).toBeNull();
    expect(cache.get("sites/2/details")).toBeNull();
    expect(cache.get("villages/1")).toEqual({ id: 1 });
  });

  it("clears all entries", () => {
    cache.set("k1", 1, 5000);
    cache.set("k2", 2, 5000);
    expect(cache.size()).toBe(2);

    cache.clear();
    expect(cache.size()).toBe(0);
    expect(cache.get("k1")).toBeNull();
  });
});
