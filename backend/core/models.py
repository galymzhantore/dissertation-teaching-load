from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class FacultyRank(Enum):
    PROFESSOR = "Professor (1st category)"
    ASSOCIATE_PROFESSOR = "Associate Professor"
    ASSISTANT_PROFESSOR = "Assistant Professor"
    SENIOR_LECTURER = "Senior Lecturer"
    SENIOR_TEACHER = "Senior Teacher"
    TEACHER = "Teacher"
    ADVISOR = "Advisor"
    TEACHER_ENGLISH = "Teacher (English medium)"
    DEAN = "Dean or Vice Dean"
    ADMIN = "Admin/Staff"


class ActivityType(Enum):
    LECTURE = "Lecture"
    PRACTICAL = "Practical"
    LAB = "Laboratory"
    SEMINAR = "Seminar"


@dataclass
class Faculty:
    id: int
    name: str
    rank: FacultyRank
    target_load: float
    max_load: float
    preferences: Dict[str, int] = field(default_factory=dict)
    qualified_courses: List[str] = field(default_factory=list)
    weight: float = 1.0
    
    def __post_init__(self):
        rank_weights = {
            FacultyRank.PROFESSOR: 1.5,
            FacultyRank.ASSOCIATE_PROFESSOR: 1.4,
            FacultyRank.ASSISTANT_PROFESSOR: 1.3,
            FacultyRank.SENIOR_LECTURER: 1.2,
            FacultyRank.SENIOR_TEACHER: 1.1,
            FacultyRank.TEACHER: 1.0,
            FacultyRank.ADVISOR: 0.8,
            FacultyRank.TEACHER_ENGLISH: 1.1,
            FacultyRank.DEAN: 1.5,
            FacultyRank.ADMIN: 0.8
        }
        self.weight = rank_weights.get(self.rank, 1.0)


@dataclass
class CourseActivity:
    id: str
    course_id: str
    course_name: str
    activity_type: ActivityType
    section_number: int
    hours: float
    student_count: int
    required_rank: Optional[FacultyRank] = None
    
    def __str__(self):
        return f"{self.course_name} ({self.activity_type.value} #{self.section_number})"


@dataclass
class Assignment:
    faculty_id: int
    activity_id: str
    preference_score: float = 0.0


@dataclass
class OptimizationResult:
    assignments: List[Assignment]
    objective_value: float
    total_deviation: float
    computation_time: float
    solver_name: str
    solver_status: str
    faculty_loads: Dict[int, float]
    unassigned_activities: List[str] = field(default_factory=list)
    is_feasible: bool = True
    gap: Optional[float] = None
    
    def get_equity_metrics(self, target_loads: Dict[int, float]) -> Dict[str, float]:
        import numpy as np
        
        deviations = []
        for faculty_id, actual_load in self.faculty_loads.items():
            target = target_loads.get(faculty_id, 0)
            deviation = abs(actual_load - target)
            deviations.append(deviation)
        
        return {
            'mean_deviation': np.mean(deviations) if deviations else 0,
            'max_deviation': max(deviations) if deviations else 0,
            'std_deviation': np.std(deviations) if deviations else 0,
            'total_deviation': sum(deviations)
        }


@dataclass
class ProblemInstance:
    faculty: List[Faculty]
    activities: List[CourseActivity]
    qualification_matrix: Dict[tuple, bool]
    name: str = "Unnamed Instance"
    metadata: Dict = field(default_factory=dict)
    
    def get_total_demand(self) -> float:
        return sum(activity.hours for activity in self.activities)
    
    def get_total_capacity(self) -> float:
        return sum(f.max_load for f in self.faculty)
    
    def check_capacity_feasibility(self) -> tuple[bool, str]:
        demand = self.get_total_demand()
        capacity = self.get_total_capacity()
        
        if demand > capacity:
            return False, f"Insufficient capacity: {demand} hours needed, {capacity} available"
        return True, "Capacity feasible"
