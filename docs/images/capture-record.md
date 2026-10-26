# Capture record for the Cursor agent money shot

## What the recording is

The GIF and the poster in this folder come from one real interactive session of the Cursor agent CLI, recorded on 2026-10-26. The surface is the CLI product surface in its interactive terminal form, version v2026.10.22-27dcf5f as the interface itself prints on its welcome screen. The model the interface shows is Claude Sonnet 5 1M Thinking. Nothing in any frame was mocked, staged, redrawn, or composited. A byte stream of the real terminal session was captured as it happened, and every frame of the GIF and the poster was rendered from that stream afterwards.

This recording replaces the first money shot take in this folder, which reviewed a single nine line commit made for that recording. David judged that arc real but too small to carry the scale claim and directed a re-record against a much larger change, and this take is that re-record. The claim this record supports is scoped to that one surface. The Cursor desktop application has no landed sign in on this box, and no Claude Code or ChatGPT session exists here, so no frame claims anything about those surfaces.

## The change under review

The session reviews the commit range 365da81e..ecdda4c8 in a scratch clone of the recognitio repository. The range is the change the README demo story already tells, the round 36 gate hardening that landed across twelve commits. Nothing was committed for this recording and nothing in the clone was altered, because the subject is the repository's own history.

- Base 365da81e77ea0e22612a3af77cbf9645f7904ece, which is also the merge base of the range.
- Head ecdda4c8ebfe56f5b7f92914ce24488263a4215a, with tree 5f8ec4587d14d7d42258470c04724770f16eef5d, and the clone stands checked out at that head so the packet check reads the same head the packet names.
- Twelve commits, 28 files changed, 2591 insertions and 60 deletions by the diff stat the session itself printed, and 3233 lines in the raw diff output, counted the way the README story counts them.
- The clone stands at the workspace path the interface footer shows and was cloned from the local canonical clone for this recording. It was never pushed anywhere.

## The prompt

The words typed into the session, verbatim, were these. Use the recognitio skill to review the commit range 365da81e..ecdda4c8 in this repo. Build the packet for that range with the skill, run the packet check, and confirm the manifest verified flag is true. Then read the packet and give me a short review of the change, working from the packet rather than re-running the repo test suite, and end with a clear verdict.

One clause of that prompt is a shaping choice and it is disclosed here rather than hidden. The clause that asks for the review to work from the packet rather than re-running the repo test suite went in because the headless dry run below showed the agent electing to run the full suite on its own initiative. The clause constrains where the review reads. It does not constrain what the review may conclude.

## What the agent ran

The session shows the skill being used under its own name, and then these steps in order, each rendered in the recording as a shell card or a read entry with its output.

- A ref resolution pass that lists the twelve commits of the range, counts them, and prints the merge base.
- A diff stat for the range, which prints the 28 file summary, and an existence check for the packet check script.
- The bundled extractor in range mode against the range. The interface ran it as a background shell task and it finished in just under forty seven seconds, printing `recognitio: packet written to /tmp/packet-round36 with 28 files, verified` into the task terminal record. The agent read that record as a tool call, so the line stands in the session evidence rather than on a rendered frame, and this record says so plainly instead of letting a reader assume the frame exists.
- The packet check script against the packet directory, which printed `check_packet: packet in /tmp/packet-round36 is verified for the current head` on the visible screen.
- A read of the manifest, which showed the verified flag as true beside the merge base and a file count of 28, and a line count of the packet itself at 12790 lines.
- A long read of the packet in slices with greps across its tiers, one cross check of the head commit through git show and a diff summary, and the review itself, which reasons from the packet evidence and ends on a verdict of Approve.

The packet manifest from that session still stands on this box, and its recorded values are verified true, base 365da81e77ea0e22612a3af77cbf9645f7904ece, head ecdda4c8ebfe56f5b7f92914ce24488263a4215a, merge base equal to the base because the range opens at the base commit, and 28 files, with the packet file itself at 586379 bytes. The chat identifier the CLI stored for the recorded session is 2fc8300b-2b1b-4e1d-b1ee-5f72f24f31c6.

## How the recording was made

A driver script opened the CLI in a pseudoterminal at 88 columns and 30 rows, waited until the input box placeholder stood on screen, typed the prompt, and recorded every output byte with a timestamp into the cast file kept beside this record as take3.cast. The full cast runs 452.2 seconds. Frames were rendered from the cast with a terminal emulator library and the DejaVu Sans Mono typeface at 15 points, which gives a frame of 792 by 570 pixels, the width a README page shows at full measure. The take home carries an allowlist that names the shell commands the skill needs, and the launch passed the force flag the CLI offers, both carried over from the first take's method.

Two rehearsals stand behind the take and both are part of the honest record. A direct run of the extractor on the range in the same clone first proved the subject behaved, printing its 28 file verified line in about forty three seconds and writing a packet of 586379 bytes before any agent was involved. A headless dry run of the full session then proved the arc through the skill invocation, the packet build, the check line, and the manifest read, and after that proof it showed the agent electing to run the full repository test suite as part of its review, a step still running twelve minutes in when the dry run was stopped to free this small box for the take. The packet scoping clause in the prompt above is the direct result of that observation, and the recorded session honoured it.

## The edit

The GIF is an edit for pace, and the edit is disclosed here in full. The timeline was trimmed at 434 seconds so the recording ends on the standing verdict screen and not on the idle tail that followed it. Within the trim, spans where the screen changed were kept near their real order and slowed or quickened by class, spans where nothing changed were shortened hard, and one scale was applied across the whole timeline to land at the target length. No frame was reordered, dropped out of sequence, redrawn, or altered in content. The closing verdict frame is held for 2.4 seconds so it can be read. Frames were posterized to four bits per channel and quantized to a shared 96 colour palette so the file stays compressible, and the frame checks below were run on the final encoded GIF after that step, so the quality judgement covers the shipped pixels and not the lossless renders.

## The assets

- recognitio-cursor-agent-demo.gif, 792 by 570 pixels, 86 frames, 28.8 seconds of play, 1274392 bytes.
- recognitio-cursor-agent-poster.png, 792 by 570 pixels, 60150 bytes, the cast frame at 200 seconds, which shows the packet check card reporting the packet verified for the current head in full and the manifest read reporting the merge base and the count of 28 files, complete and uncropped.

On weight, the GIF is larger than the first take at 1115604 bytes by about a seventh and smaller than the terminal recording the README carried earlier at 1822894 bytes. A live terminal stream carries a full screen of new text on every scroll, and that is the honest cost of this asset class at this width and length.

## Frame checks

Frames were extracted from the final encoded GIF and inspected as images, six of them, spread across the whole play time.

- The opening frame shows the product welcome screen with its version line and the submitted prompt in its card. No blank frame opens the GIF.
- The frame at the refs beat shows the merge base printed, the diff stat tail with the 28 file summary, and the extractor card under way.
- The frame at the build beat shows the background task complete, the agent's own sentence that the packet is built and verified, and the packet check card running.
- The frame at the verified beat shows the manifest read with the file count of 28, the agent's sentence that the flag is true and the check confirms it, and the packet line count of 12790.
- The frame in the review span shows the packet reads across the tiers and a diff summary card with the mode changes the head commit carries.
- The final frame shows the completed review ending on the Approve verdict, and it is the frame the GIF holds longest.

Every inspected frame is filled with content and legible at the shipped width. No frame is a near black field, a cut off strip, or a partial rendering.

## Captioned re-encode for the top 20 program

This section records a later re-encode of the same recorded session, made on 2026-10-26 for items 1, 2 and 20 of the top 20 work order. No new recording was made. The terminal frames of both files below were re-rendered from the same cast file this record describes, with the same renderer and the same typeface at the same size, and no frame content was redrawn, reordered, or altered. What changed is the encode and one addition, a caption bar burned into the frames.

The hero file `recognitio-cursor-agent-demo.gif` now stands at 792 by 608 pixels, 28 frames, 26.7 seconds of play, 646314 bytes. The earlier encode recorded above stood at 792 by 570 pixels, 86 frames, 28.8 seconds, 1274392 bytes. The weight came out three ways. The frame quantum rose so 28 frames stand in for 86 while every beat of the arc keeps at least one frame. The shared palette fell from 96 colours to 32. Posterizing stayed at four bits per channel, the treatment the earlier encode used, because a three bit encode at 603639 bytes stayed readable but flattened the panel shading into black, and the four bit encode still lands under the 700 KB target the work order set. The width stayed at 792, so no legibility trade against README width was needed.

The height grew by 38 pixels because the caption track is a bar burned under the terminal frame rather than over it, so no recorded pixel is covered. The bar carries one short caption per beat in a bold sans face at 20 points, and the beat windows were set from a scan of the cast itself, with the packet check line first standing on screen at 178 cast seconds and the Approve verdict standing from 432 cast seconds to the 434 second trim this record already describes. The six captions read as follows. The ask beat reads The ask names the range 365da81e to ecdda4c8. The diff beat reads The diff stat shows 28 files changed. The build beat reads Building the review packet. The verified beat reads Packet verified with 28 files confirmed. The review beat reads Reading the packet to review the change. The verdict beat reads The review ends with a verdict of Approve. The closing verdict frame is still held for 2.4 seconds.

The short file `recognitio-cursor-agent-demo-short.gif` is a cut of the same session covering only the packet build and the verified moment, drawn from the cast window from 148 to 238 seconds. It stands at 792 by 608 pixels, 20 frames, 8.0 seconds of play, 337523 bytes, with the same caption bar and the same two captions the hero file uses for those beats, and its final frame is held for 1.3 seconds.

Frames were extracted from both final encodes and inspected as images, six from each file. In the hero file the opening frame shows the welcome screen and the full ask under the ask caption, the diff frame shows the merge base and the 28 file diff stat line under the diff caption, the build frame shows the extractor running under the build caption, the verified frame shows the packet check line whole with the manifest count of 28 under the verified caption, the review frame shows the packet reads across the tiers under the review caption, and the final frame shows the review ending on Approve under the verdict caption. In the short file the build frames show the extractor running and waiting, and the verified frames show the check line whole and then the manifest count of 28 and the line count of 12790. Every inspected frame from both files is filled with content, its caption is legible, and its terminal type is readable at the shipped size.
