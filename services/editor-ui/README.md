# Editor UI

This is a lightweight Next.js + TypeScript scaffold for the STEMpathize editor and digest viewer. It reads generated digests and machine-readable JSON from the repository's data/ folder and renders a think-tank quality UI for exploring conflicts and hedging guidance.

Local dev
1. cd services/editor-ui
2. npm install
3. npm run dev

Build
1. npm run build
2. npm start

Notes
- The UI reads data from ../../data to keep the digest generation and frontend in the same repository. In production you may want to serve digests from an API or object store and change the data loading accordingly.
