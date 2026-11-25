# Status — 2026-11-25

## Latest direction

The user criticized the first animation as not looking like proper animation,
then explicitly instructed us to use authored phoneme poses as a starting point.
This supersedes the earlier request to ignore those keys. Continue toward
natural articulation while preserving the chosen visual identity.

Hardware: CM4 + Hailo-8, denser Sigma WS35 side displays. OpenSeeFace measures
the wearer. Prioritize animation; leave hardware and ROS integration until later.
No tongue or tooth rows. Keep reference data and inspection notes private.

## Visual failures found

The legacy raster-ribbon path inflated a closed symbol, retained an angular
lower crease, shifted the whole design sideways and clipped some openings.
Slow filtering plus a squared seal gate also swallowed short vowel openings.
Those failures were confirmed by enlarged frame review and tracing controls.
Do not present the legacy path or test counts as evidence of naturalness.

An automatic contour-corrective trial produced tearing and was discarded.
The current baseline preserves authored topology and uses bounded blend weights.

## Current implementation

- Generic private morph import: indexed geometry, UVs, configured sparse pose
  targets, emission texture and fixed view bounded across the mouth basis.
- Schema-2 renderer: continuous authored-mesh blendspace with proper occlusion,
  anatomical side depth and texture sampling. Older silhouette mode is legacy.
- Nonnegative open/round/spread weights form a convex primary mouth basis.
  Opening has a stronger bounded response. Expressions and blinks are separate.
- Contact suppresses opening exactly and detaches with an 8 ms time constant.
  The additional squared seal gate was removed.
- Native review tools render the same private compiled mesh and Python-generated
  weights as the WebGL path. They do not require source-specific names in code.
- Current private runtime files use the authored-mesh format under ignored local/.
  Public code contains no source assets, private mappings or derived geometry.

## Verification

- Python unittest: 22 passed.
- Node geometry/character/morph tests: 13 passed.
- Tests include convex weights, closed/full authored endpoints, prompt contact
  release, sparse pose application, unchanged source data and side projection.
- CLI/HTTP smoke passed for the authored rig, texture endpoint, renderer modules
  and both side-output routes. All rendered face pixels stayed inside the
  fixed review frame throughout the new clip.
- Enlarged render sequences were inspected; tearing trials were rejected.
- Browser runtime and physical-panel appearance remain unverified. CM4 latency
  and frame rate are unmeasured. Tests do not establish perceptual naturalness.

## Earlier core and integration

OpenSeeFace binary decoding, face selection, signed robust calibration,
monotonic freshness and tracking-loss relaxation remain independently usable.
See PIPELINE.md for the existing proto-ros2 path; that repository is unchanged.
Future integration should consume its existing measurements and preserve screen
ownership rather than starting another production UDP receiver.

## Repository and privacy

Public project: https://github.com/infopcgood/prootface, branch master.
Previous checkpoint: 3bb66f0b3c80cf690865edeb23da9193bd298317.
Publish generic code, tests and documentation only. Private source identifiers,
object/key names, settings, textures, meshes and inspection notes stay out of
public commits. Use an expected branch SHA and preserve concurrent changes.

## Next

1. Review the authored-basis speaking animation against the earlier failure.
2. Refine intermediate poses and timing from visual feedback; do not assume
   that either raw source poses or a passing-test count establish naturalness.
3. Test the same model with real OpenSeeFace wearer speech and tune calibration.
4. Exercise both sides in a real browser and on the visor.
5. Only then add measured LED mapping, ROS adaptation and CM4 profiling.
