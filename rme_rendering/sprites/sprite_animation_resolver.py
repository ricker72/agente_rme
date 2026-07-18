from __future__ import annotations

from dataclasses import asdict, dataclass

from ..appearance_dat_flags import SpriteAnimationInfo, SpritePhaseTiming


@dataclass(frozen=True)
class AnimationFrameResult:
    frame: int
    elapsed_ms: int
    phase_duration_ms: int
    timing_source: str

    def to_dict(self) -> dict[str, int | str]:
        return asdict(self)


class SpriteAnimationResolver:
    """Deterministic equivalent of Canary's Animator for viewport and QA use."""

    def resolve(
        self,
        animation: SpriteAnimationInfo,
        elapsed_ms: int,
        fallback_frames: int = 1,
        seed: int = 0,
    ) -> AnimationFrameResult:
        frame_count = max(1, animation.frame_count, int(fallback_frames))
        if frame_count <= 1:
            return AnimationFrameResult(0, max(0, elapsed_ms), 0, "STATIC")
        if not animation.phases:
            return AnimationFrameResult(
                max(0, elapsed_ms) % frame_count,
                max(0, elapsed_ms),
                1,
                "FRAME_TICK_FALLBACK",
            )

        start = int(animation.default_start_phase)
        if animation.random_start_phase or start < 0 or start >= frame_count:
            start = self._stable_seed(seed) % frame_count
        start %= frame_count
        sequence = self._sequence(frame_count, animation.loop_type, start)
        durations = [self._duration(animation, frame, seed) for frame in sequence]
        elapsed = max(0, int(elapsed_ms))
        cycle_duration = sum(durations)

        if animation.loop_type == 1 and animation.loop_count > 0:
            total_duration = cycle_duration * animation.loop_count
            if elapsed >= total_duration:
                frame = sequence[-1]
                return AnimationFrameResult(frame, elapsed, durations[-1], "DAT_COUNTED_COMPLETE")
        if cycle_duration > 0:
            elapsed %= cycle_duration
        for frame, duration in zip(sequence, durations):
            if elapsed < duration:
                source = "DAT_SYNCHRONIZED" if animation.synchronized else "DAT_ASYNCHRONOUS"
                return AnimationFrameResult(frame, max(0, elapsed_ms), duration, source)
            elapsed -= duration
        return AnimationFrameResult(sequence[-1], max(0, elapsed_ms), durations[-1], "DAT_TIMING")

    def _sequence(self, frame_count: int, loop_type: int, start: int) -> list[int]:
        forward = list(range(start, frame_count)) + list(range(0, start))
        if loop_type != -1 or frame_count <= 2:
            return forward
        pingpong = list(range(frame_count)) + list(range(frame_count - 2, 0, -1))
        offset = pingpong.index(start)
        return pingpong[offset:] + pingpong[:offset]

    def _duration(self, animation: SpriteAnimationInfo, frame: int, seed: int) -> int:
        phase = animation.phases[frame]
        low = max(1, int(phase.duration_min or phase.duration_max or 1))
        high = max(low, int(phase.duration_max or low))
        if high == low:
            return low
        return low + ((self._stable_seed(seed + frame * 131) % (high - low + 1)))

    def _stable_seed(self, value: int) -> int:
        value = int(value) & 0xFFFFFFFF
        value ^= value >> 16
        value = (value * 0x7FEB352D) & 0xFFFFFFFF
        value ^= value >> 15
        return value


def animation_info_from_dict(value: object) -> SpriteAnimationInfo:
    if not isinstance(value, dict):
        return SpriteAnimationInfo()
    phases = tuple(
        SpritePhaseTiming(
            duration_min=int(phase.get("duration_min", 0) or 0),
            duration_max=int(phase.get("duration_max", 0) or 0),
        )
        for phase in value.get("phases", [])
        if isinstance(phase, dict)
    )
    return SpriteAnimationInfo(
        default_start_phase=int(value.get("default_start_phase", 0) or 0),
        synchronized=bool(value.get("synchronized", False)),
        random_start_phase=bool(value.get("random_start_phase", False)),
        loop_type=int(value.get("loop_type", 0) or 0),
        loop_count=int(value.get("loop_count", 0) or 0),
        phases=phases,
    )
