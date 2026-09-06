# RakshakGIS API Client & Server-State Layer (Chunk M5-03)

The `@/lib/api` module provides the centralized, typed HTTP client and declarative server-state foundation for all RakshakGIS frontend modules.

## 1. Backend API Base URL Configuration

The API client reads the backend URL from the environment variable:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

- **Production/Staging:** Configured via deployment environment variables.
- **Local Development:** Default fallback is `http://localhost:8000/api/v1`.
- **Normalization:** Trailing and leading slashes are automatically stripped to eliminate accidental double slashes (e.g. `//sites`).

---

## 2. Making Typed API Requests

Use the singleton `apiClient` for imperative requests:

```typescript
import { apiClient } from "@/lib/api";
import { CandidateSiteRead } from "@/types/sites";

// GET request with typed response and query params
const sites = await apiClient.get<CandidateSiteRead[]>("/sites", {
  params: { district_id: 1, limit: 10 },
});

// POST request with JSON payload
const newEvaluation = await apiClient.post("/sites/evaluate", {
  site_id: 42,
  scenario_id: "heavy_monsoon",
});
```

### Supported HTTP Methods
- `apiClient.get<T>(path, options)`
- `apiClient.post<T>(path, body, options)`
- `apiClient.put<T>(path, body, options)`
- `apiClient.patch<T>(path, body, options)`
- `apiClient.delete<T>(path, options)`
- `apiClient.request<T>(path, method, options)`

---

## 3. Automatic Authentication Integration

All requests automatically inject the current active JWT Bearer token from Chunk M5-02 session storage:

```http
Authorization: Bearer <access_token>
```

- **Opt-Out for Public Endpoints:** Pass `{ auth: false }` in `RequestOptions` (e.g. login, health checks).
- **Security:** Tokens are never logged, never exposed in URLs, and never included in public DOM attributes.

---

## 4. Standardized Error Normalization (M2-04)

All API and networking failures throw a strongly-typed `ApiError`:

```typescript
import { apiClient, ApiError } from "@/lib/api";

try {
  await apiClient.get("/protected-route");
} catch (error) {
  if (error instanceof ApiError) {
    console.error(error.message);      // Sanitized user-safe message
    console.error(error.status);       // HTTP status code (401, 403, 404, 422, etc.)
    console.error(error.code);         // M2-04 machine error code (e.g. UNAUTHORIZED)
    console.error(error.requestId);    // Correlation ID (x-request-id)
    
    if (error.isNetworkError) {
      // Offline / network failure
    }
    if (error.isAborted) {
      // Request cancelled via AbortSignal
    }
  }
}
```

---

## 5. Server-State & Data-Fetching Hooks

For React components, use declarative hooks that automatically handle loading states, error states, and request cancellation:

### `useApiQuery`

```typescript
import { useApiQuery, apiClient } from "@/lib/api";

function VillageList({ districtId }: { districtId: number }) {
  const { data, isLoading, isError, error, refetch } = useApiQuery(
    `villages-${districtId}`,
    (signal) => apiClient.get(`/villages`, { params: { district_id: districtId }, signal }),
    {
      cacheTtlMs: 30000, // Optional 30s in-memory cache
      enabled: Boolean(districtId),
    }
  );

  if (isLoading) return <div>Loading habitations...</div>;
  if (isError) return <div>Error: {error?.message}</div>;

  return <div>{/* Render habitations */}</div>;
}
```

### `useApiMutation`

```typescript
import { useApiMutation, apiClient } from "@/lib/api";

function AssignRelocationButton({ siteId }: { siteId: number }) {
  const { mutate, isLoading } = useApiMutation(
    (vars: { villageId: number }, signal) =>
      apiClient.post("/relocation/assign", vars, { signal }),
    {
      onSuccess: (data) => console.log("Assigned", data),
    }
  );

  return (
    <button onClick={() => mutate({ villageId: 101 })} disabled={isLoading}>
      {isLoading ? "Assigning..." : "Confirm Relocation"}
    </button>
  );
}
```

---

## 6. Request Cancellation & Race Safety

When query parameters change rapidly (e.g. user toggling regions, filtering villages, or panning a GIS map), `useApiQuery` automatically aborts the preceding in-flight request via `AbortController` and discards outdated responses to prevent stale state overwrites.
