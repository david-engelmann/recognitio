# Recognitio showcase

A static web page that presents what recognitio does and shows its real
output, built with Next.js and React and exported as plain files that any
static host can serve.

## What it shows

The page walks a visitor through the problem, the packet, the receipt and
the install routes in about a minute. Every figure and every quoted line on
it comes from one real packet shipped in this repository at
examples/example-packet-991ac6a, the packet for commit 991ac6a, regenerated
and verified by the repo gates. The change tier lets the visitor step
through the four tiers of that packet and open one of its hunks with more
or less of its real context.

This page is showcase material. It dresses the proof and never stands in
for it. The proof stands in the repository, in the shipped example packet,
its manifest and the recorded sessions the README links.

## Build

```bash
npm install
npm run build
```

The build writes the static export into out/. Serve that folder with any
static host. The page makes no network calls at view time and carries no
analytics.

## Layout

- app/page.tsx holds the page and its copy
- app/data/packet.ts holds the figures and excerpts drawn from the shipped
  packet, each with its provenance stated in the file
- app/components holds the tier stepper and the hunk viewer
- The build record for this page stands with the work that produced it,
  outside this folder
