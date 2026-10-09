from flask import Flask, render_template, request, jsonify
from distilled_water_assessor import (
    DistilledWaterAssessor,
    WaterQualityMetrics,
    DistilledWaterCategory,
)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template(
        "index.html",
        categories=[category.value for category in DistilledWaterCategory],
        result=None,
        error=None,
    )


@app.route("/assess", methods=["POST"])
def assess():
    try:
        metrics = WaterQualityMetrics(
            ph_level=float(request.form["ph_level"]),
            electrical_conductivity=float(request.form["electrical_conductivity"]),
            total_dissolved_solids=float(request.form["total_dissolved_solids"]),
            turbidity=float(request.form["turbidity"]),
            chloride_content=float(request.form["chloride_content"]),
            heavy_metal_concentration=float(request.form["heavy_metal_concentration"]),
            microbial_count=int(request.form["microbial_count"]),
            organic_matter_content=float(request.form["organic_matter_content"]),
        )

        selected = request.form.get("category")
        category = None
        if selected:
            try:
                category = DistilledWaterCategory(selected)
            except ValueError:
                category = None

        assessor = DistilledWaterAssessor()
        result = assessor.assess(metrics, category)

        return render_template(
            "index.html",
            categories=[category.value for category in DistilledWaterCategory],
            result=result,
            error=None,
        )
    except Exception as exc:
        return render_template(
            "index.html",
            categories=[category.value for category in DistilledWaterCategory],
            result=None,
            error=f"Assessment failed: {exc}",
        ), 400


@app.route("/api/assess", methods=["POST"])
def api_assess():
    data = request.get_json(silent=True) or {}
    try:
        metrics = WaterQualityMetrics(
            ph_level=float(data.get("ph_level", 0)),
            electrical_conductivity=float(data.get("electrical_conductivity", 0)),
            total_dissolved_solids=float(data.get("total_dissolved_solids", 0)),
            turbidity=float(data.get("turbidity", 0)),
            chloride_content=float(data.get("chloride_content", 0)),
            heavy_metal_concentration=float(data.get("heavy_metal_concentration", 0)),
            microbial_count=int(data.get("microbial_count", 0)),
            organic_matter_content=float(data.get("organic_matter_content", 0)),
        )

        category_name = data.get("category")
        category = None
        if category_name:
            try:
                category = DistilledWaterCategory(category_name)
            except ValueError:
                category = None

        result = DistilledWaterAssessor().assess(metrics, category)
        return jsonify(
            {
                "category": result.category.value,
                "grade": result.grade.value,
                "score": round(result.score, 2),
                "passing_parameters": result.passing_parameters,
                "failing_parameters": result.failing_parameters,
                "recommendations": result.recommendations,
            }
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
