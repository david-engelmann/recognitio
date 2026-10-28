# Verifier completeness readings

This file carries the packet check readings that decide a stamp where the skill text points at it. Every reading here is a reading the shipped packet check performs, stated so a reviewer can tell what a verified stamp does and does not cover.

## The change tier

The check rebuilds the change tier whole from the recount, with the extractor builder that wrote it, and compares the text line for line. The tier introduction, the prose inside a file section outside its diff fence, and every other line of the tier are compared on the same terms as the diff bodies, so no prose can stand in the change tier that the builder did not write.

## The diff fence

Each per file diff in the change tier stands inside a fence the extractor sizes one backtick longer than the longest backtick run inside that diff with a floor of three, and the check reads the block back under the same rule. The change tier reading opens a diff block on a run of three or more backticks followed by the word diff, closes it only on a line exactly equal to that opening run, and compares the opening run against the size the body it fences requires, one backtick longer than the longest run inside the body with a floor of three, refusing a fence of any other size. A diff body can hold a bare fence line as context, as the diff of a Markdown file that holds a code block does, and under a fixed three backtick fence that line closes the block early for every reader tracking fence state, so later file headings read as fenced text and the check reports files as missing from a packet that holds them. The sized fence cannot be closed from inside the body it fences. The section and heading readings track the packet fences under the wider fence rule, where a run at least as long as an opening run, standing alone on its line apart from surrounding whitespace, closes that fence, while the change tier reading holds a diff block to the exact run that opened it. A packet written under the old fixed fence still stamps wherever its diff bodies hold no run of three or more backticks anywhere, and a packet whose bodies hold such a run stamps once it is regenerated under the sized fence.

## The Contents line

The builder writes a plain Contents line between the packet header and its contents block, and the header and contents rebuilds stand on that line as their marker. A packet whose Contents line is missing or damaged is refused. The two rebuilds are never silently skipped, because a stamp that issued while they were skipped would say less than its wording claims.

## Pull request references

In pull request mode the check reads the record the GitHub CLI reports for the pull request under review. The title and the body are ground truth for the triage rebuild, the spec references are recomputed from that body, and the base and head identifiers in the same record are compared against the base and head the manifest records. A pull request retargeted to another base, or a head branch moved on the host, therefore refuses the stamp while the CLI answers. No identifier the record carries is fetched and left unread, and the branch names the record also offers are not requested, because no surface in the pair records a branch name for them to be compared against.

## The body fence

When no CLI answers, the body is read back out of the packet and the triage tier is rebuilt from it. A body that cannot be read back takes the presence only reading, where the title line and the spec reference line and the state line are asked to stand, only where the packet carries the cap line the builder writes for a capped body. A body whose fence is damaged or missing, with no cap line standing, is refused. A mutation of the packet alone never converts the whole rebuild into the weaker reading in silence.

## The findings path

A relative findings path in the recorded command resolves beside the packet directory, in the directory that holds the packet directory, and never against the working directory the check was launched from. The packet directory is a sealed pair and a findings file cannot lawfully stand inside it, so a relative spelling names a file beside the pair. The same packet and the same findings file give the same verdict from every directory, and a file that merely shares the spelling in the launch directory is never read.

## The creation time

The manifest creation time is read against the repository the check runs against. A creation time naming a moment more than one hour before the recorded head commit was committed is refused, because a packet cannot have been extracted from a commit before that commit existed. A creation time naming a moment more than one hour after the check runs is refused on the same terms. The one hour each way is the stated allowance for clock skew between the machine that committed the head, the machine that ran the extraction, and the machine that runs the check, and it replaces the earlier one day of silent grace. A creation time inside the allowance is accepted as a clock reading and is not presented as proved to the minute.

## Pull request state

The extractor records the state of the pull request under review as the CLI reported it at fetch time, with the fetch moment standing beside it, in the triage tier and in the manifest pull request record. The packet words that state as a snapshot from that fetch and never as a live claim. The check rebuilds the state line from the manifest record and never refuses a packet because the live state has since moved, because a moved state does not falsify a snapshot that names its own moment. The fetch moment is held inside the same bounds as the creation time, so a state cannot have been fetched before the change it names existed or after the run that recorded it. The history tier words the states of prior pull requests as a snapshot from the fetch that built the packet on the same terms, and those states are not refreshed after that fetch.
