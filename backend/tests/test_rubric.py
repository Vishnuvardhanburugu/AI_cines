from app.services.prompt_analysis.rubric import material_gaps_for_category, score_prompt_quality


def test_short_prompt_scores_lower_than_specific():
    weak = "Make a video of a futuristic city."
    strong = (
        "Create a cinematic video of a futuristic city at night with neon lighting, "
        "a slow tracking camera shot, atmospheric haze, and photorealistic style."
    )
    assert score_prompt_quality(weak, "video") < score_prompt_quality(strong, "video")


def test_material_gaps_for_video():
    gaps = material_gaps_for_category("Make a video of a car.", "video")
    assert "camera" in gaps or "environment" in gaps or "atmosphere" in gaps


def test_fluff_alone_does_not_win():
    fluff = "Create a stunning beautiful amazing incredible awesome video."
    specific = "Create a video of a rainy Tokyo street with a slow tilt-up camera shot."
    assert score_prompt_quality(specific, "video") >= score_prompt_quality(fluff, "video")
