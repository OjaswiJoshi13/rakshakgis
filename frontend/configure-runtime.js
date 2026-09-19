/**
 * Configure Next.js Standalone Runtime Proxy Destinations
 *
 * Reads .next/routes-manifest.template.json, safely parses JSON,
 * replaces backend proxy origin with BACKEND_INTERNAL_URL (default: http://backend:8000),
 * and idempotently writes .next/routes-manifest.json.
 *
 * This ensures:
 * 1. Safe JSON parsing/serialization (no sed regex delimiter collisions or escaping issues)
 * 2. Idempotent container restarts (always reads from the immutable template)
 * 3. Support for dynamic runtime environment variables in standalone mode
 */
const fs = require('fs');
const path = require('path');

const templatePath = path.join(__dirname, '.next', 'routes-manifest.template.json');
const targetPath = path.join(__dirname, '.next', 'routes-manifest.json');

if (fs.existsSync(templatePath)) {
  try {
    const raw = fs.readFileSync(templatePath, 'utf8');
    const manifest = JSON.parse(raw);
    const backendUrl = (process.env.BACKEND_INTERNAL_URL || 'http://backend:8000').replace(/\/+$/, '');

    if (Array.isArray(manifest.rewrites)) {
      manifest.rewrites = manifest.rewrites.map((r) => {
        if (typeof r.destination === 'string') {
          return {
            ...r,
            destination: r.destination.replace(/^https?:\/\/[^/]+/, backendUrl),
          };
        }
        return r;
      });
    }

    fs.writeFileSync(targetPath, JSON.stringify(manifest, null, 2), 'utf8');
  } catch (err) {
    console.error('Failed to configure runtime routes-manifest:', err);
  }
}
