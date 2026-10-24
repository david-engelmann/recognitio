// Host side tests for the Build 7 mod. Run with
// claude plugin test from the plugin directory, with no session,
// sign in, or network. Each test drives the exported hook
// functions directly with stub arguments, the way the test kit
// drives events through hooks.

import { test, expect } from "claude-code/testing";
import { gateSpawn, catchSpawnFailure } from "./register.js";

const VERIFIED = JSON.stringify({ verified: true, files: [] });
const UNVERIFIED = JSON.stringify({ verified: false, files: [] });

function stubDollar(
  env: Record<string, string | undefined>,
  files: Record<string, string>,
) {
  return {
    env: {
      get: async (name: string) => env[name],
    },
    fs: {
      read: async ({ path }: { path: string }) => {
        if (!(path in files)) {
          throw new Error("no such file: " + path);
        }
        return files[path];
      },
    },
  };
}

const passthrough = async (e: any) => ({ passed: e });
const event = { agentId: "reviewer-1" };

test("an unverified packet denies the review spawn", async () => {
  const $ = stubDollar(
    { RECOGNITIO_PACKET_DIR: "/packet" },
    { "/packet/manifest.json": UNVERIFIED },
  );
  const result: any = await gateSpawn($, event, passthrough);
  expect(typeof result.deny).toBe("string");
  expect(result.deny).toContain("not verified");
});

test("a verified packet lets the spawn through", async () => {
  const $ = stubDollar(
    { RECOGNITIO_PACKET_DIR: "/packet" },
    { "/packet/manifest.json": VERIFIED },
  );
  const result: any = await gateSpawn($, event, passthrough);
  expect(result).toEqual({ passed: event });
});

test("no packet configured leaves the spawn alone", async () => {
  const $ = stubDollar({}, {});
  const result: any = await gateSpawn($, event, passthrough);
  expect(result).toEqual({ passed: event });
});

test("an unreadable manifest fails closed through the catch handler", async () => {
  const $ = stubDollar({ RECOGNITIO_PACKET_DIR: "/packet" }, {});
  let denied: any = null;
  try {
    await gateSpawn($, event, passthrough);
  } catch (err) {
    denied = await catchSpawnFailure($, event, passthrough);
  }
  expect(denied).not.toBe(null);
  expect(denied.deny).toContain("denied rather than let through");
});

test("a corrupt manifest fails closed through the catch handler", async () => {
  const $ = stubDollar(
    { RECOGNITIO_PACKET_DIR: "/packet" },
    { "/packet/manifest.json": "not json{{{" },
  );
  let denied: any = null;
  try {
    await gateSpawn($, event, passthrough);
  } catch (err) {
    denied = await catchSpawnFailure($, event, passthrough);
  }
  expect(denied).not.toBe(null);
  expect(denied.deny).toContain("denied rather than let through");
});

test("the catch handler denies without judging", async () => {
  const $ = stubDollar({}, {});
  const result: any = await catchSpawnFailure($, event, passthrough);
  expect(typeof result.deny).toBe("string");
  expect(result.deny).toContain("denied rather than let through");
});
