"""Tests for BlueprintEmbeddingEngine."""

from core.blueprints.blueprint import Blueprint, BlueprintTile, BlueprintMetadata
from core.blueprint_intelligence.blueprint_embedding_engine import (
    BlueprintEmbeddingEngine,
)


class TestBlueprintEmbeddingEngine:
    """Test embedding extraction and feature calculation."""

    def setup_method(self):
        self.engine = BlueprintEmbeddingEngine()

    def _make_bp(
        self,
        name="test",
        category="hunt",
        size=(10, 10),
        tiles=None,
        rooms=None,
        zones=None,
        tags=None,
        raw=None,
        entry=None,
    ):
        bp = Blueprint(
            name=name,
            category=category,
            size=size,
            tiles=tiles or [],
            rooms=rooms or [],
            zones=zones or [],
            metadata=BlueprintMetadata(tags=tags or []),
            _raw=raw or {},
        )
        if entry:
            bp.entry = entry
        return bp

    def test_embed_basic_blueprint(self):
        """Test basic embedding produces correct vector."""
        bp = self._make_bp(
            "roshamuul_hunt", "hunt", tiles=[BlueprintTile(x=0, y=0, ground=100)]
        )
        emb = self.engine.embed(bp)
        assert emb.blueprint_name == "roshamuul_hunt"
        assert emb.blueprint_category == "hunt"
        assert len(emb.vector) == 12
        assert all(0.0 <= v <= 1.0 for v in emb.vector)

    def test_embed_tile_density(self):
        """Test tile density calculation."""
        tiles = [BlueprintTile(x=x, y=0, ground=100) for x in range(5)]
        bp = self._make_bp("test", "hunt", size=(10, 10), tiles=tiles)
        emb = self.engine.embed(bp)
        assert 0.0 <= emb.tile_density <= 1.0

    def test_embed_caches_result(self):
        """Test embedding is cached."""
        bp = self._make_bp("cache_test")
        emb1 = self.engine.embed(bp)
        emb2 = self.engine.embed(bp)
        assert emb1 is emb2

    def test_embed_clear_cache(self):
        """Test clearing cache."""
        bp = self._make_bp("cache_clear")
        emb1 = self.engine.embed(bp)
        self.engine.clear_cache()
        emb2 = self.engine.embed(bp)
        assert emb1 is not emb2

    def test_embed_all(self):
        """Test batch embedding."""
        bps = [self._make_bp(f"bp_{i}") for i in range(3)]
        embeddings = self.engine.embed_all(bps)
        assert len(embeddings) == 3

    def test_embed_with_rooms(self):
        """Test embedding a descriptive blueprint with rooms."""
        bp = self._make_bp(
            "city_test", "city", rooms=[{"name": "room1"}, {"name": "room2"}]
        )
        emb = self.engine.embed(bp)
        assert emb.room_count > 0.0

    def test_embed_with_zones_branching(self):
        """Test branch factor from zones."""
        zones = [
            {"type": "zone", "connections": ["zone2", "zone3"]},
            {"type": "zone", "connections": ["zone1"]},
            {"type": "zone", "connections": ["zone1", "zone2"]},
        ]
        bp = self._make_bp("branched", zones=zones)
        emb = self.engine.embed(bp)
        assert emb.branch_factor >= 0.0

    def test_embed_with_entry(self):
        """Test connectivity with entry point."""
        bp = self._make_bp("has_entry", entry=(5, 5))
        emb = self.engine.embed(bp)
        assert emb.connectivity > 0.5

    def test_embed_spawn_density(self):
        """Test spawn density calculation."""
        tiles = [
            BlueprintTile(x=0, y=0, ground=100, spawn={"monster": "rat"}),
            BlueprintTile(x=1, y=0, ground=100),
        ]
        bp = self._make_bp("spawns", tiles=tiles)
        emb = self.engine.embed(bp)
        assert emb.spawn_density > 0.0
        assert emb.spawn_density <= 1.0

    def test_embed_city_services(self):
        """Test city services from tags."""
        bp = self._make_bp("city_test", "city", tags=["depot", "temple", "market"])
        emb = self.engine.embed(bp)
        assert emb.city_services > 0.0

    def test_embed_critic_and_playtest(self):
        """Test embedding extracts critic and playtest scores."""
        bp = self._make_bp("scored", raw={"critic_score": 85.0, "playtest_score": 72.0})
        emb = self.engine.embed(bp)
        assert emb.critic_score == 0.85
        assert emb.playtest_score == 0.72

    def test_similarity_to(self):
        """Test embedding similarity."""
        bp_a = self._make_bp("a")
        bp_b = self._make_bp("b")
        emb_a = self.engine.embed(bp_a)
        emb_b = self.engine.embed(bp_b)
        sim = emb_a.similarity_to(emb_b)
        assert 0.0 <= sim <= 1.0

    def test_clamp_values(self):
        """Test that values are clamped to [0, 1]."""
        from core.blueprint_intelligence.models.blueprint_embedding import (
            BlueprintEmbedding,
        )

        emb = BlueprintEmbedding(tile_density=1.5, room_count=-0.5)
        assert emb.tile_density == 1.0
        assert emb.room_count == 0.0

    def test_cosine_similarity_identical(self):
        """Test cosine similarity of identical vectors."""
        from core.blueprint_intelligence.models.blueprint_embedding import (
            BlueprintEmbedding,
        )

        v = [0.5, 0.3, 0.8, 0.1, 0.6, 0.2, 0.0, 0.9, 0.4, 0.7, 0.5, 0.3]
        sim = BlueprintEmbedding.cosine_similarity(v, v)
        assert abs(sim - 1.0) < 0.0001

    def test_cosine_similarity_orthogonal(self):
        """Test cosine similarity of orthogonal vectors."""
        from core.blueprint_intelligence.models.blueprint_embedding import (
            BlueprintEmbedding,
        )

        v1 = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        sim = BlueprintEmbedding.cosine_similarity(v1, v2)
        assert abs(sim) < 0.0001

    def test_embed_to_dict_roundtrip(self):
        """Test serialization roundtrip."""
        bp = self._make_bp(
            "roundtrip", "city", tiles=[BlueprintTile(x=0, y=0, ground=100)]
        )
        emb = self.engine.embed(bp)
        data = emb.to_dict()
        assert data["blueprint_name"] == "roundtrip"
        assert "vector" in data

    def test_embed_empty_blueprint(self):
        """Test embedding an empty blueprint."""
        bp = self._make_bp("empty")
        emb = self.engine.embed(bp)
        assert emb is not None
        # connectivity has a default of 0.3, so not all will be 0
        assert emb.tile_density == 0.0
        assert emb.room_count == 0.0

    def test_embed_waypoints_from_raw(self):
        """Test waypoint extraction from raw."""
        bp = self._make_bp(
            "wps", raw={"waypoints": [{"x": 0, "y": 0}, {"x": 1, "y": 1}]}
        )
        emb = self.engine.embed(bp)
        assert emb.waypoint_count > 0.0
