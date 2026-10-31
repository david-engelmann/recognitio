# Contributing

Recognitio is built by its owner, working with a team of
agents, and work lands on `main` by direct push under the
conventions in AGENTS.md. Outside pull requests are not
taken. The reason stands in the open here, so nobody has
to learn it from a failed check after doing the work.

Every non-merge commit a person puts on a pull request
must carry one exact `Signed-off-by` trailer naming the
owner of this repo, and the DCO job in the continuous
integration workflow refuses any other value on those
commits. The job does not run at all when the actor on
the pull request is dependabot[bot], and merge commits
stand outside the list of commits it checks. That
trailer is the owner
attesting to his own commits, and nobody else can
honestly sign his name to theirs. The sign off flag the
failure message suggests adds the identity of the person
who runs it, so that remedy cannot produce the required
value for anyone but the owner.

Defect reports are welcome, and they are the route in.
Open an issue through the bug report template and name
what happened and what should have happened, the mode
and input the run covered, and the manifest the run
wrote. A packet that claimed verified and was not whole
is the most serious report this repo takes. A fix
described in an issue, with the evidence behind it, can
be picked up by the owner and landed under his own sign
off.
