/**
 * Lightweight In-Memory API Cache
 * Provides cache storage with TTL expiration for disaster GIS queries.
 */

interface CacheEntry<T = unknown> {
  data: T;
  timestamp: number;
  ttlMs: number;
}

export class ApiCache {
  private cache = new Map<string, CacheEntry>();

  public get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const isExpired = Date.now() - entry.timestamp > entry.ttlMs;
    if (isExpired) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  public set<T>(key: string, data: T, ttlMs: number): void {
    if (ttlMs <= 0) return;
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttlMs,
    });
  }

  public invalidate(key: string): void {
    this.cache.delete(key);
  }

  public invalidatePattern(pattern: RegExp | string): void {
    const regex = typeof pattern === "string" ? new RegExp(pattern) : pattern;
    this.cache.forEach((_, key) => {
      if (regex.test(key)) {
        this.cache.delete(key);
      }
    });
  }

  public clear(): void {
    this.cache.clear();
  }

  public size(): number {
    return this.cache.size;
  }
}

export const apiCache = new ApiCache();
