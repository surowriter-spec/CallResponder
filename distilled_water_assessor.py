"""
Distilled Water Category and Assessment Program

This module provides a comprehensive system for categorizing and assessing
distilled water based on various quality parameters and standards.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


class WaterQualityGrade(Enum):
    """Quality grades for distilled water assessment"""
    EXCELLENT = "Excellent"
    GOOD = "Good"
    ACCEPTABLE = "Acceptable"
    POOR = "Poor"
    FAILED = "Failed"


class DistilledWaterCategory(Enum):
    """Categories of distilled water based on purity and use"""
    LABORATORY_GRADE = "Laboratory Grade"
    PHARMACEUTICAL_GRADE = "Pharmaceutical Grade"
    INDUSTRIAL_GRADE = "Industrial Grade"
    COSMETIC_GRADE = "Cosmetic Grade"
    FOOD_GRADE = "Food Grade"
    STANDARD = "Standard"


@dataclass
class WaterQualityMetrics:
    """Data class for water quality metrics"""
    ph_level: float
    electrical_conductivity: float  # µS/cm
    total_dissolved_solids: float  # mg/L
    turbidity: float  # NTU
    chloride_content: float  # mg/L
    heavy_metal_concentration: float  # mg/L
    microbial_count: int  # CFU/mL
    organic_matter_content: float  # mg/L
    
    def is_valid(self) -> bool:
        """Validate all metrics are within reasonable ranges"""
        return (
            0 <= self.ph_level <= 14 and
            0 <= self.electrical_conductivity <= 10000 and
            0 <= self.total_dissolved_solids <= 5000 and
            0 <= self.turbidity <= 100 and
            0 <= self.chloride_content <= 1000 and
            0 <= self.heavy_metal_concentration <= 100 and
            0 <= self.microbial_count <= 1000000 and
            0 <= self.organic_matter_content <= 100
        )


@dataclass
class AssessmentResult:
    """Assessment result with detailed analysis"""
    category: DistilledWaterCategory
    grade: WaterQualityGrade
    score: float  # 0-100
    metrics: WaterQualityMetrics
    passing_parameters: List[str]
    failing_parameters: List[str]
    recommendations: List[str]
    assessment_date: datetime
    
    def __str__(self) -> str:
        """String representation of assessment result"""
        return (
            f"Assessment Result\n"
            f"Category: {self.category.value}\n"
            f"Grade: {self.grade.value}\n"
            f"Score: {self.score:.1f}/100\n"
            f"Date: {self.assessment_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Passing Parameters: {', '.join(self.passing_parameters)}\n"
            f"Failing Parameters: {', '.join(self.failing_parameters)}\n"
            f"Recommendations: {'; '.join(self.recommendations)}"
        )


class DistilledWaterAssessor:
    """Main class for assessing distilled water quality and category"""
    
    # Quality standards for each category (strict to lenient)
    STANDARDS = {
        DistilledWaterCategory.PHARMACEUTICAL_GRADE: {
            "ph_min": 5.5, "ph_max": 6.5,
            "ec_max": 5.1,  # µS/cm
            "tds_max": 2.5,  # mg/L
            "turbidity_max": 0.1,  # NTU
            "chloride_max": 0.10,  # mg/L
            "heavy_metals_max": 0.001,  # mg/L
            "microbial_max": 10,  # CFU/mL
            "organic_max": 0.5  # mg/L
        },
        DistilledWaterCategory.LABORATORY_GRADE: {
            "ph_min": 5.0, "ph_max": 7.0,
            "ec_max": 10.0,
            "tds_max": 5.0,
            "turbidity_max": 0.5,
            "chloride_max": 0.5,
            "heavy_metals_max": 0.01,
            "microbial_max": 100,
            "organic_max": 1.0
        },
        DistilledWaterCategory.FOOD_GRADE: {
            "ph_min": 6.0, "ph_max": 7.5,
            "ec_max": 50.0,
            "tds_max": 25.0,
            "turbidity_max": 1.0,
            "chloride_max": 1.0,
            "heavy_metals_max": 0.05,
            "microbial_max": 1000,
            "organic_max": 2.0
        },
        DistilledWaterCategory.COSMETIC_GRADE: {
            "ph_min": 5.5, "ph_max": 7.5,
            "ec_max": 75.0,
            "tds_max": 50.0,
            "turbidity_max": 2.0,
            "chloride_max": 2.0,
            "heavy_metals_max": 0.1,
            "microbial_max": 5000,
            "organic_max": 3.0
        },
        DistilledWaterCategory.INDUSTRIAL_GRADE: {
            "ph_min": 4.0, "ph_max": 8.0,
            "ec_max": 200.0,
            "tds_max": 100.0,
            "turbidity_max": 5.0,
            "chloride_max": 5.0,
            "heavy_metals_max": 0.5,
            "microbial_max": 50000,
            "organic_max": 5.0
        },
        DistilledWaterCategory.STANDARD: {
            "ph_min": 3.0, "ph_max": 9.0,
            "ec_max": 500.0,
            "tds_max": 250.0,
            "turbidity_max": 10.0,
            "chloride_max": 10.0,
            "heavy_metals_max": 1.0,
            "microbial_max": 100000,
            "organic_max": 10.0
        }
    }
    
    def __init__(self):
        """Initialize the assessor"""
        self.assessment_history: List[AssessmentResult] = []
    
    def assess(self, metrics: WaterQualityMetrics, 
               category: Optional[DistilledWaterCategory] = None) -> AssessmentResult:
        """
        Assess water quality and determine category/grade
        
        Args:
            metrics: WaterQualityMetrics object with test results
            category: Optional specific category to assess against
                     If None, will auto-detect best matching category
        
        Returns:
            AssessmentResult with detailed analysis
        """
        if not metrics.is_valid():
            raise ValueError("Invalid metrics: values out of acceptable ranges")
        
        # Auto-detect category if not specified
        if category is None:
            category = self._determine_category(metrics)
        
        # Evaluate against standards
        passing_params, failing_params, parameter_scores = self._evaluate_parameters(
            metrics, category
        )
        
        # Calculate overall score and grade
        score = self._calculate_score(parameter_scores)
        grade = self._determine_grade(score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            failing_params, category, metrics
        )
        
        result = AssessmentResult(
            category=category,
            grade=grade,
            score=score,
            metrics=metrics,
            passing_parameters=passing_params,
            failing_parameters=failing_params,
            recommendations=recommendations,
            assessment_date=datetime.now()
        )
        
        self.assessment_history.append(result)
        return result
    
    def _determine_category(self, metrics: WaterQualityMetrics) -> DistilledWaterCategory:
        """Determine the best matching category for given metrics"""
        categories_ranked = []
        
        for category in DistilledWaterCategory:
            passing, failing, _ = self._evaluate_parameters(metrics, category)
            match_score = len(passing) - len(failing) * 2
            categories_ranked.append((category, match_score))
        
        categories_ranked.sort(key=lambda x: x[1], reverse=True)
        return categories_ranked[0][0]
    
    def _evaluate_parameters(self, metrics: WaterQualityMetrics, 
                            category: DistilledWaterCategory) -> tuple:
        """
        Evaluate if metrics pass standards for a category
        
        Returns:
            Tuple of (passing_params, failing_params, parameter_scores)
        """
        standards = self.STANDARDS[category]
        passing = []
        failing = []
        scores = {}
        
        # pH evaluation
        if standards["ph_min"] <= metrics.ph_level <= standards["ph_max"]:
            passing.append("pH Level")
            scores["pH"] = 100.0
        else:
            failing.append("pH Level")
            scores["pH"] = self._calculate_deviation_score(
                metrics.ph_level, standards["ph_min"], standards["ph_max"]
            )
        
        # Electrical Conductivity evaluation
        if metrics.electrical_conductivity <= standards["ec_max"]:
            passing.append("Electrical Conductivity")
            scores["EC"] = 100.0
        else:
            failing.append("Electrical Conductivity")
            scores["EC"] = max(0, 100 - (metrics.electrical_conductivity - standards["ec_max"]) * 2)
        
        # TDS evaluation
        if metrics.total_dissolved_solids <= standards["tds_max"]:
            passing.append("Total Dissolved Solids")
            scores["TDS"] = 100.0
        else:
            failing.append("Total Dissolved Solids")
            scores["TDS"] = max(0, 100 - (metrics.total_dissolved_solids - standards["tds_max"]) * 2)
        
        # Turbidity evaluation
        if metrics.turbidity <= standards["turbidity_max"]:
            passing.append("Turbidity")
            scores["Turbidity"] = 100.0
        else:
            failing.append("Turbidity")
            scores["Turbidity"] = max(0, 100 - (metrics.turbidity - standards["turbidity_max"]) * 5)
        
        # Chloride evaluation
        if metrics.chloride_content <= standards["chloride_max"]:
            passing.append("Chloride Content")
            scores["Chloride"] = 100.0
        else:
            failing.append("Chloride Content")
            scores["Chloride"] = max(0, 100 - (metrics.chloride_content - standards["chloride_max"]) * 10)
        
        # Heavy Metals evaluation
        if metrics.heavy_metal_concentration <= standards["heavy_metals_max"]:
            passing.append("Heavy Metal Concentration")
            scores["Heavy Metals"] = 100.0
        else:
            failing.append("Heavy Metal Concentration")
            scores["Heavy Metals"] = max(0, 100 - (metrics.heavy_metal_concentration - standards["heavy_metals_max"]) * 50)
        
        # Microbial evaluation
        if metrics.microbial_count <= standards["microbial_max"]:
            passing.append("Microbial Count")
            scores["Microbial"] = 100.0
        else:
            failing.append("Microbial Count")
            ratio = metrics.microbial_count / standards["microbial_max"]
            scores["Microbial"] = max(0, 100 - (ratio - 1) * 20)
        
        # Organic Matter evaluation
        if metrics.organic_matter_content <= standards["organic_max"]:
            passing.append("Organic Matter Content")
            scores["Organic"] = 100.0
        else:
            failing.append("Organic Matter Content")
            scores["Organic"] = max(0, 100 - (metrics.organic_matter_content - standards["organic_max"]) * 10)
        
        return passing, failing, scores
    
    def _calculate_deviation_score(self, value: float, min_val: float, 
                                  max_val: float) -> float:
        """Calculate score based on deviation from acceptable range"""
        if value < min_val:
            deviation = min_val - value
        else:
            deviation = value - max_val
        
        return max(0, 100 - deviation * 10)
    
    def _calculate_score(self, parameter_scores: Dict[str, float]) -> float:
        """Calculate overall assessment score from parameter scores"""
        if not parameter_scores:
            return 0.0
        return sum(parameter_scores.values()) / len(parameter_scores)
    
    def _determine_grade(self, score: float) -> WaterQualityGrade:
        """Determine grade based on score"""
        if score >= 90:
            return WaterQualityGrade.EXCELLENT
        elif score >= 75:
            return WaterQualityGrade.GOOD
        elif score >= 60:
            return WaterQualityGrade.ACCEPTABLE
        elif score >= 40:
            return WaterQualityGrade.POOR
        else:
            return WaterQualityGrade.FAILED
    
    def _generate_recommendations(self, failing_params: List[str],
                                 category: DistilledWaterCategory,
                                 metrics: WaterQualityMetrics) -> List[str]:
        """Generate recommendations based on failing parameters"""
        recommendations = []
        
        if not failing_params:
            recommendations.append("Water meets all standards for the category.")
            return recommendations
        
        param_recommendations = {
            "pH Level": "Adjust pH level using appropriate buffers or acids/bases.",
            "Electrical Conductivity": "Conduct additional distillation or deionization to reduce dissolved ions.",
            "Total Dissolved Solids": "Implement reverse osmosis or multi-stage filtration.",
            "Turbidity": "Use fine filtration or sedimentation to reduce suspended particles.",
            "Chloride Content": "Perform ion-exchange chromatography or additional purification.",
            "Heavy Metal Concentration": "Use chelation therapy or advanced oxidation processes.",
            "Microbial Count": "Apply UV sterilization, autoclaving, or membrane filtration.",
            "Organic Matter Content": "Use activated carbon filtration or oxidative treatment."
        }
        
        for param in failing_params:
            if param in param_recommendations:
                recommendations.append(param_recommendations[param])
        
        # Category-specific recommendations
        if category == DistilledWaterCategory.PHARMACEUTICAL_GRADE:
            recommendations.append("Consider moving to a certified pharmaceutical water supplier.")
        elif category == DistilledWaterCategory.LABORATORY_GRADE:
            recommendations.append("Verify distillation equipment is properly maintained.")
        
        recommendations.append(f"Re-test after implementing corrections within 48 hours.")
        
        return recommendations
    
    def get_assessment_history(self) -> List[AssessmentResult]:
        """Get all assessment results"""
        return self.assessment_history
    
    def get_category_summary(self) -> Dict[DistilledWaterCategory, int]:
        """Get summary of assessed categories"""
        summary = {cat: 0 for cat in DistilledWaterCategory}
        for result in self.assessment_history:
            summary[result.category] += 1
        return {k: v for k, v in summary.items() if v > 0}


def main():
    """Example usage of the Distilled Water Assessor"""
    assessor = DistilledWaterAssessor()
    
    # Example 1: High quality pharmaceutical-grade water
    print("=" * 60)
    print("Example 1: Pharmaceutical Grade Assessment")
    print("=" * 60)
    metrics_pharma = WaterQualityMetrics(
        ph_level=6.0,
        electrical_conductivity=3.5,
        total_dissolved_solids=1.8,
        turbidity=0.05,
        chloride_content=0.08,
        heavy_metal_concentration=0.0005,
        microbial_count=5,
        organic_matter_content=0.3
    )
    result_pharma = assessor.assess(metrics_pharma, DistilledWaterCategory.PHARMACEUTICAL_GRADE)
    print(result_pharma)
    
    # Example 2: Laboratory grade water
    print("\n" + "=" * 60)
    print("Example 2: Laboratory Grade Assessment")
    print("=" * 60)
    metrics_lab = WaterQualityMetrics(
        ph_level=5.8,
        electrical_conductivity=8.5,
        total_dissolved_solids=4.2,
        turbidity=0.3,
        chloride_content=0.4,
        heavy_metal_concentration=0.008,
        microbial_count=80,
        organic_matter_content=0.8
    )
    result_lab = assessor.assess(metrics_lab)
    print(result_lab)
    
    # Example 3: Industrial grade water
    print("\n" + "=" * 60)
    print("Example 3: Industrial Grade Assessment")
    print("=" * 60)
    metrics_industrial = WaterQualityMetrics(
        ph_level=6.5,
        electrical_conductivity=150.0,
        total_dissolved_solids=75.0,
        turbidity=3.5,
        chloride_content=3.0,
        heavy_metal_concentration=0.3,
        microbial_count=30000,
        organic_matter_content=2.5
    )
    result_industrial = assessor.assess(metrics_industrial)
    print(result_industrial)
    
    # Summary
    print("\n" + "=" * 60)
    print("Assessment Summary")
    print("=" * 60)
    summary = assessor.get_category_summary()
    for category, count in summary.items():
        print(f"{category.value}: {count} assessment(s)")


if __name__ == "__main__":
    main()
