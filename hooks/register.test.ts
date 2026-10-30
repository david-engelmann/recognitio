// Host side tests for the Build 7 mod. Run with
// claude plugin test from the plugin directory, with no session,
// sign in, or network. Each test fires the agent.spawn event
// through the loaded module the way the host fires it in a
// session, and the kit answers the mods API calls the hook
// makes in the documented shapes, so a call site the host
// would refuse or misread fails here the way it fails live.
// The engine side stub answers a passed spawn with the model
// shape the events reference names for agent.spawn.

import { test, expect, mock } from "claude-code/testing";

const VERIFIED = JSON.stringify({ verified: true, files: [] });
const UNVERIFIED = JSON.stringify({ verified: false, files: [] });

function stubManifest(on: any, body: string) {
  on("fs.read", ($: any, e: any) => ({
    value: e.path.endsWith("manifest.json") ? body : "",
  }));
}

function stubEngineSpawn(on: any) {
  on("agent.spawn", () => ({ model: "stub-model" }));
}

const event = { agentId: "reviewer-1" };

test("an unverified packet denies the review spawn", async ($, on) => {
  mock.env(on, { RECOGNITIO_PACKET_DIR: "/packet" });
  stubManifest(on, UNVERIFIED);
  stubEngineSpawn(on);
  const result: any = await $.agent.spawn(event);
  expect(typeof result.deny).toBe("string");
  expect(result.deny).toContain("not verified");
});

test("a verified packet lets the spawn through", async ($, on) => {
  mock.env(on, { RECOGNITIO_PACKET_DIR: "/packet" });
  stubManifest(on, VERIFIED);
  stubEngineSpawn(on);
  const result: any = await $.agent.spawn(event);
  expect(result).toEqual({ model: "stub-model" });
});

test("no packet configured leaves the spawn alone", async ($, on) => {
  mock.env(on, {});
  stubEngineSpawn(on);
  const result: any = await $.agent.spawn(event);
  expect(result).toEqual({ model: "stub-model" });
});

test("an unreadable manifest fails closed through the catch handler", async ($, on) => {
  mock.env(on, { RECOGNITIO_PACKET_DIR: "/packet" });
  on("fs.read", () => ({ deny: "no such file" }));
  stubEngineSpawn(on);
  const result: any = await $.agent.spawn(event);
  expect(typeof result.deny).toBe("string");
  expect(result.deny).toContain("denied rather than let through");
});

test("a corrupt manifest fails closed through the catch handler", async ($, on) => {
  mock.env(on, { RECOGNITIO_PACKET_DIR: "/packet" });
  stubManifest(on, "not json{{{");
  stubEngineSpawn(on);
  const result: any = await $.agent.spawn(event);
  expect(typeof result.deny).toBe("string");
  expect(result.deny).toContain("denied rather than let through");
});

test("a verified flag that is not true denies the spawn", async ($, on) => {
  mock.env(on, { RECOGNITIO_PACKET_DIR: "/packet" });
  stubManifest(on, JSON.stringify({ verified: "yes", files: [] }));
  stubEngineSpawn(on);
  const result: any = await $.agent.spawn(event);
  expect(typeof result.deny).toBe("string");
  expect(result.deny).toContain("not verified");
});

test("a packet directory with a trailing slash still gates", async ($, on) => {
  mock.env(on, { RECOGNITIO_PACKET_DIR: "/packet/" });
  stubManifest(on, VERIFIED);
  stubEngineSpawn(on);
  const result: any = await $.agent.spawn(event);
  expect(result).toEqual({ model: "stub-model" });
});

test("a manifest that is not an object denies the spawn", async ($, on) => {
  mock.env(on, { RECOGNITIO_PACKET_DIR: "/packet" });
  stubManifest(on, JSON.stringify("verified"));
  stubEngineSpawn(on);
  const result: any = await $.agent.spawn(event);
  expect(typeof result.deny).toBe("string");
  expect(result.deny).toContain("not verified");
});
