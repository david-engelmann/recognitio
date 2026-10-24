// Build 7, the Claude Code mod with in process hooks.
//
// The mod gates the reviewer fan out at spawn time. Its agent.spawn
// hook reads the review packet manifest named by RECOGNITIO_PACKET_DIR
// and denies the spawn unless the manifest reads verified. A hook
// crash fails closed through the .catch handler, which returns the
// deny shape for agent.spawn. Decision 4 binds the mod like every
// other build, so the hook applies the shipped deterministic rule,
// the manifest verified flag, and never a model judgment.
//
// What the mod does not do is stated in the open. The hook sees only
// in session agent spawns. Reviewers the runbook starts as claude -p
// subprocesses are gated by scripts/check_fanout.py, not by this mod.
// If this mod's own .catch handler threw or timed out, the host would
// skip the hook as if it had no handler and the spawn would proceed.
// That second layer fail open is a recorded limit, not a surprise.
// See docs/mod-build7.md for the full brief.

const PACKET_ENV = "RECOGNITIO_PACKET_DIR";

async function packetIsVerified($, packetDir) {
  const manifestPath = packetDir.replace(/\/+$/, "") + "/manifest.json";
  const text = await $.fs.read({ path: manifestPath });
  const manifest = JSON.parse(typeof text === "string" ? text : text.value);
  return (
    manifest !== null &&
    typeof manifest === "object" &&
    manifest.verified === true
  );
}

async function gateSpawn($, e, next) {
  const packetDir = await $.env.get(PACKET_ENV);
  if (typeof packetDir !== "string" || packetDir.length === 0) {
    return next(e);
  }
  if (await packetIsVerified($, packetDir)) {
    return next(e);
  }
  return {
    deny: "recognitio: the review packet manifest is not verified, so this review spawn is denied",
  };
}

function catchSpawnFailure($, e, next) {
  return {
    deny: "recognitio: the packet gate hook failed, so this review spawn is denied rather than let through",
  };
}

export function register(on, options) {
  on("agent.spawn", gateSpawn).catch(catchSpawnFailure);
}

export { gateSpawn, catchSpawnFailure };
