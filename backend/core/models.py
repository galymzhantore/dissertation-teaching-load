from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class FacultyRank(Enum):
    """
    Оқытушы лауазымдары - Х. Досмұхамедов атындағы Атырау университеті
    ережесіне сәйкес (2024-2025 оқу жылы)
    """
    PROFESSOR = "Профессор"
    ASSOCIATE_PROFESSOR = "Доцент"
    ASSISTANT_PROFESSOR = "Қауымдастырылған профессор"
    SENIOR_LECTURER = "Аға оқытушы"
    SENIOR_TEACHER = "Аға оқытушы"
    TEACHER = "Оқытушы"
    ADVISOR = "Эдвайзер"
    TEACHER_ENGLISH = "Оқытушы (ағылшын тілінде)"
    DEAN = "Декан/Декан орынбасары"
    ADMIN = "Әкімшілік қызметкер"


class ActivityType(Enum):
    """Оқу белсенділігінің түрлері"""
    LECTURE = "Дәріс"
    PRACTICAL = "Практикалық"
    LAB = "Зертханалық"
    SEMINAR = "Семинар"


class DayOfWeek(Enum):
    """Апта күндері (5 күн)"""
    MONDAY = "Дүйсенбі"
    TUESDAY = "Сейсенбі"
    WEDNESDAY = "Сәрсенбі"
    THURSDAY = "Бейсенбі"
    FRIDAY = "Жұма"


class RoomType(Enum):
    """Аудитория түрлері"""
    LECTURE_HALL = "Дәрісхана"
    CLASSROOM = "Аудитория"
    COMPUTER_LAB = "Компьютер класы"
    LABORATORY = "Зертхана"


@dataclass
class TimeSlot:
    """
    Сабақ уақыты (пара)
    1 академиялық сағат = 50 минут
    """
    id: int
    name: str
    start_time: str
    end_time: str
    
    @classmethod
    def get_standard_slots(cls) -> List['TimeSlot']:
        """Стандартты 8 пара"""
        return [
            cls(1, "1-пара", "08:00", "08:50"),
            cls(2, "2-пара", "09:00", "09:50"),
            cls(3, "3-пара", "10:00", "10:50"),
            cls(4, "4-пара", "11:00", "11:50"),
            cls(5, "5-пара", "12:00", "12:50"),
            cls(6, "6-пара", "14:00", "14:50"),
            cls(7, "7-пара", "15:00", "15:50"),
            cls(8, "8-пара", "16:00", "16:50"),
        ]


@dataclass
class Room:
    """Аудитория"""
    id: str
    name: str
    room_type: RoomType
    capacity: int
    building: str = "Бас корпус"
    
    def can_fit(self, student_count: int) -> bool:
        return self.capacity >= student_count


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
    """Тағайындау - оқытушыны белсенділікке тағайындау"""
    faculty_id: int
    activity_id: str
    preference_score: float = 0.0


@dataclass
class ScheduledActivity:
    """
    Кесте жазбасы - толық расписание ақпараты
    """
    activity_id: str
    faculty_id: int
    day: DayOfWeek
    time_slot: TimeSlot
    room_id: str
    course_name: str = ""
    activity_type: ActivityType = ActivityType.LECTURE
    hours: float = 1.0
    
    def to_dict(self) -> dict:
        return {
            "activity_id": self.activity_id,
            "faculty_id": self.faculty_id,
            "day": self.day.value,
            "time_slot": self.time_slot.name,
            "time": f"{self.time_slot.start_time}-{self.time_slot.end_time}",
            "room_id": self.room_id,
            "course_name": self.course_name,
            "activity_type": self.activity_type.value,
            "hours": self.hours
        }


@dataclass 
class Timetable:
    """
    Толық кесте - барлық тағайындаулар мен расписание
    """
    scheduled_activities: List[ScheduledActivity] = field(default_factory=list)
    rooms: List[Room] = field(default_factory=list)
    
    def get_faculty_schedule(self, faculty_id: int) -> List[ScheduledActivity]:
        """Оқытушының жеке кестесі"""
        return [s for s in self.scheduled_activities if s.faculty_id == faculty_id]
    
    def get_room_schedule(self, room_id: str) -> List[ScheduledActivity]:
        """Аудиторияның кестесі"""
        return [s for s in self.scheduled_activities if s.room_id == room_id]
    
    def get_day_schedule(self, day: DayOfWeek) -> List[ScheduledActivity]:
        """Күннің кестесі"""
        return [s for s in self.scheduled_activities if s.day == day]
    
    def check_conflicts(self) -> List[str]:
        """Қақтығыстарды тексеру"""
        conflicts = []
        
        # Оқытушы қақтығыстары
        for i, s1 in enumerate(self.scheduled_activities):
            for s2 in self.scheduled_activities[i+1:]:
                if (s1.faculty_id == s2.faculty_id and 
                    s1.day == s2.day and 
                    s1.time_slot.id == s2.time_slot.id):
                    conflicts.append(f"Оқытушы {s1.faculty_id}: {s1.day.value} {s1.time_slot.name}")
        
        # Аудитория қақтығыстары
        for i, s1 in enumerate(self.scheduled_activities):
            for s2 in self.scheduled_activities[i+1:]:
                if (s1.room_id == s2.room_id and 
                    s1.day == s2.day and 
                    s1.time_slot.id == s2.time_slot.id):
                    conflicts.append(f"Аудитория {s1.room_id}: {s1.day.value} {s1.time_slot.name}")
        
        return conflicts


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
