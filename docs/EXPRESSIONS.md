# Expression-specific speech

Expressions are selected externally. Camera measurements continue to control
articulation; they do not classify or switch the selected emotion.

The first bank set is neutral, happy, angry, sad and unamused. Each expression
has a closed/rest, open, wide and rounded mouth endpoint. Eye targets are
independent. Runtime blends between speech endpoints inside the selected bank
and crossfades between banks when a command arrives.

## External commands

HTTP buttons can send:

```sh
curl -X POST http://127.0.0.1:8080/api/expression \
  -H 'Content-Type: application/json' -d '{"expression":"angry"}'
```

The default command latches until the next selection or process restart. It does
not change live/manual/demo mode, reset calibration, or restart the speech
controller. Optional fields: part (`face`, `mouth`, `eyes`), transition (seconds,
0–2; default 0.2), and hold (seconds, 0–3600; default 0 means latched). A positive
hold temporarily overrides the latched choice, then fades back. Repeated
identical commands do not restart the transition or extend that temporary hold.
Interrupted transitions start from the current mixed pose.

ROS uses the existing interface_pkg/FacialExpression message, without changing
its definition:

```sh
ros2 topic pub --once /facial_expression interface_pkg/msg/FacialExpression \
  '{type: emotion, expression: angry, override_time: 0.0}'
```

`type=emotion` or `face` selects both channels. `mouth` and `eyes` select one
channel independently. `override_time=0` latches; positive values are temporary.
The aliases idle and smile map to neutral and happy. Other legacy PNG or phoneme
names are not guessed into expressions. Unknown/unavailable names are rejected.
The topic and transition duration are parameters of prootface_pkg only.

## Composition and timing

The unchanged causal speech controller runs at 24 Hz, including opening contrast,
family commitment, observed-onset accents, contact holds and stale-input handling.
Presentation remains 24/12/6 fps with held poses. A preset crossfade takes about
five controller ticks by default; the browser adds no extra interpolation.

For expression e and speech endpoint p, the unrestrained compiled shape correction is:

`context[e,p] = authored_shape[e,p] - rest_offset[e]`

The rendered mouth combines the ordinary speech basis with the expression's
rest offset and its speech-weighted context corrections. Consequently a rounded
endpoint can relax a smiling rest contour differently from an open endpoint.
Authored mouth targets supply the expression identity. Curvature fields may
refine those shapes but cannot be the sole content of an expression bank.

Optional motion scaling compiles into a separate articulation correction:
`motion[e,p] = (motion_scale[e,p] - 1) * neutral_endpoint_delta[p]`.
Only this motion correction receives the anterior speech restraint. The
authored shape and its rest cancellation remain independent of that restraint,
so a restrained front edge cannot weaken or leave residual emotional corners.

Measured smile/frown additives fade out as an externally selected mouth bank
fades in. Articulation and the enhanced rounding-reach channel remain active.
Full lip contact zeros open/wide/round context weights. Blinks attenuate the
expression eye targets and retain their clean full-closure endpoint. Tracking
loss eases speech to rest while preserving the external expression selection.
The explicit optional consonant channels retain their ordinary speech targets
plus the expression rest correction; this first set authors the four primary
camera-driven endpoints rather than a complete phoneme inventory.

## Private compilation and compatibility

Schema-2 characters opt in with expression_sets. Each non-neutral entry maps
rest, open, round, wide, eye_left and eye_right to existing sparse target names.
Optional open_motion, round_motion and wide_motion references supply separate
articulation corrections. The optional front_targets array names targets that
use the same anterior motion restraint as ordinary speech targets. Generic sparse
rendering handles the compiled targets in both EGL and WebGL.

`prootface.expression_rig.compile_expression_sets(character, definitions)` builds
these banks offline. Each definition contains mouth/rest, mouth/open, mouth/round
and mouth/wide specifications, plus eyes/left and eyes/right target references.
Mouth specifications accept sources (named target weights), motion_scale (three
axis gains), bend and slope (normalized field curvature). A bank must include a
nonzero source mouth contribution; curve-only definitions are rejected. When
motion_scale is one, no additional motion target is needed. The importer reads
these definitions from private settings after compiling the ordinary rig and
optional mouth corrections. Original geometry, artistic values and source-key
mappings remain private. Compile the full endpoints and inspect transitions,
closures and occlusion on the actual character before delivery. Compare the
compiled rest poses directly with the source mouth targets, then review the
speech poses with neutral eyes as well as full faces. Do not assume an authored
mouth target exists for every emotion label; derived combinations must be
identified as such in the private art settings and review notes.

Older characters remain usable with neutral only. A missing bank is reported;
changing the Python code cannot create missing character geometry. Use a newly
compiled private character/texture pair to enable the additional expressions.
No new model inference or accelerator backend is needed.
