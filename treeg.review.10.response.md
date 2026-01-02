# Code Author Response: treeg.py (review 10)

Thanks for the review. I focused on the remaining wide-node performance concern and left the rest as-is.

## Accepted
1) **Wide-node quadratic behaviour**: Agreed. I changed the frame’s `cleaned` accumulator to a `list[Node]`, append in-place in `_attach_child`, and materialise a tuple in `_finalise_frame`. This removes the O(k²) tuple growth for star-shaped trees while keeping behaviour unchanged.

## Pushback / Clarification
- **Frame.children type tightening**: I did not change `Frame`’s children element type, consistent with your caution. With the current validation-on-visit strategy and tests that inject invalid children, keeping `tuple[object, ...]` remains the accurate contract. No change made here.

## Verification
- `just format`
- `just lint`
- `just test`

All gates are green.
