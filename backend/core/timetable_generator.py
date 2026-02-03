"""
Кесте генераторы - Оңтайландыру нәтижелерінен расписание құру

Х. Досмұхамедов атындағы Атырау университеті
"""

import random
from typing import List, Dict, Optional
from dataclasses import dataclass

from backend.core.models import (
    ProblemInstance, OptimizationResult, Assignment,
    ScheduledActivity, Timetable, Room, RoomType,
    TimeSlot, DayOfWeek, ActivityType, CourseActivity
)


class TimetableGenerator:
    """
    Оңтайландыру нәтижелерін толық расписаниеге айналдыру
    """
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.time_slots = TimeSlot.get_standard_slots()
        self.days = list(DayOfWeek)
        
    def generate_rooms(self, count: int = 20) -> List[Room]:
        """Аудиториялар тізімін генерациялау"""
        rooms = []
        
        # Дәрісханалар (үлкен аудиториялар)
        for i in range(1, count // 4 + 1):
            rooms.append(Room(
                id=f"LH{i:02d}",
                name=f"{100 + i}-дәрісхана",
                room_type=RoomType.LECTURE_HALL,
                capacity=random.choice([100, 120, 150, 200]),
                building="Бас корпус"
            ))
        
        # Аудиториялар (орташа)
        for i in range(1, count // 2 + 1):
            rooms.append(Room(
                id=f"CR{i:02d}",
                name=f"{200 + i}-аудитория",
                room_type=RoomType.CLASSROOM,
                capacity=random.choice([30, 35, 40]),
                building="Бас корпус"
            ))
        
        # Компьютер кластары
        for i in range(1, count // 6 + 1):
            rooms.append(Room(
                id=f"CL{i:02d}",
                name=f"{300 + i}-компьютер класы",
                room_type=RoomType.COMPUTER_LAB,
                capacity=25,
                building="Бас корпус"
            ))
        
        # Зертханалар
        for i in range(1, count // 6 + 1):
            rooms.append(Room(
                id=f"LB{i:02d}",
                name=f"{400 + i}-зертхана",
                room_type=RoomType.LABORATORY,
                capacity=20,
                building="Бас корпус"
            ))
        
        return rooms
    
    def generate_timetable(
        self,
        instance: ProblemInstance,
        result: OptimizationResult,
        rooms: Optional[List[Room]] = None
    ) -> Timetable:
        """
        Оңтайландыру нәтижелерінен толық кесте құру
        """
        if rooms is None:
            rooms = self.generate_rooms()
        
        timetable = Timetable(rooms=rooms)
        
        # Оқытушы бос уақыты
        faculty_schedule: Dict[int, Dict[str, set]] = {}
        # Аудитория бос уақыты
        room_schedule: Dict[str, Dict[str, set]] = {}
        
        # Инициализация
        for f in instance.faculty:
            faculty_schedule[f.id] = {day.name: set() for day in self.days}
        for r in rooms:
            room_schedule[r.id] = {day.name: set() for day in self.days}
        
        # Белсенділіктерді кестеге орналастыру
        for assignment in result.assignments:
            activity = next(
                (a for a in instance.activities if a.id == assignment.activity_id),
                None
            )
            if not activity:
                continue
                
            faculty = next(
                (f for f in instance.faculty if f.id == assignment.faculty_id),
                None
            )
            if not faculty:
                continue
            
            # Жетекшілік және ғылыми жұмыстарды кестеге қоспау
            if activity.activity_type in [
                ActivityType.BACHELOR_THESIS, 
                ActivityType.MASTER_THESIS, 
                ActivityType.RESEARCH_NIRM
            ]:
                continue
            
            # Қолайлы аудитория табу
            suitable_room = self._find_suitable_room(
                activity, rooms, room_schedule, faculty_schedule, assignment.faculty_id
            )
            
            if suitable_room is None:
                continue
                
            room, day, slot = suitable_room
            
            # Кестеге қосу
            scheduled = ScheduledActivity(
                activity_id=activity.id,
                faculty_id=assignment.faculty_id,
                day=day,
                time_slot=slot,
                room_id=room.id,
                course_name=activity.course_name,
                activity_type=activity.activity_type,
                hours=activity.hours
            )
            
            timetable.scheduled_activities.append(scheduled)
            
            # Бүлуды жаңарту
            faculty_schedule[assignment.faculty_id][day.name].add(slot.id)
            room_schedule[room.id][day.name].add(slot.id)
        
        return timetable
    
    def _find_suitable_room(
        self,
        activity: CourseActivity,
        rooms: List[Room],
        room_schedule: Dict[str, Dict[str, set]],
        faculty_schedule: Dict[int, Dict[str, set]],
        faculty_id: int
    ) -> Optional[tuple]:
        """
        Белсенділікке қолайлы аудитория, күн және уақыт табу
        """
        # Белсенділік түріне сәйкес аудитория түрі
        room_type_map = {
            ActivityType.LECTURE: [RoomType.LECTURE_HALL, RoomType.CLASSROOM],
            ActivityType.PRACTICAL: [RoomType.CLASSROOM],
            ActivityType.LAB: [RoomType.LABORATORY, RoomType.COMPUTER_LAB],
            ActivityType.SEMINAR: [RoomType.CLASSROOM]
        }
        
        preferred_types = room_type_map.get(
            activity.activity_type, 
            [RoomType.CLASSROOM]
        )
        
        # Қолайлы аудиторияларды іздеу
        suitable_rooms = [
            r for r in rooms 
            if r.room_type in preferred_types and r.can_fit(activity.student_count)
        ]
        
        if not suitable_rooms:
            suitable_rooms = [r for r in rooms if r.can_fit(activity.student_count)]
        
        if not suitable_rooms:
            suitable_rooms = rooms  # Кез келген аудитория
        
        # Бос уақыт іздеу
        random.shuffle(suitable_rooms)
        days_shuffled = self.days.copy()
        random.shuffle(days_shuffled)
        
        for room in suitable_rooms:
            for day in days_shuffled:
                for slot in self.time_slots:
                    # Аудитория бос болса
                    if slot.id in room_schedule[room.id][day.name]:
                        continue
                    # Оқытушы бос болса
                    if slot.id in faculty_schedule[faculty_id][day.name]:
                        continue
                    
                    return (room, day, slot)
        
        # Бос уақыт табылмады
        return None


def create_timetable_dataframe(timetable: Timetable, instance: ProblemInstance):
    """
    Кестені pandas DataFrame форматына айналдыру
    """
    import pandas as pd
    
    data = []
    for scheduled in timetable.scheduled_activities:
        faculty = next(
            (f for f in instance.faculty if f.id == scheduled.faculty_id),
            None
        )
        room = next(
            (r for r in timetable.rooms if r.id == scheduled.room_id),
            None
        )
        
        data.append({
            "Күн": scheduled.day.value,
            "Уақыт": f"{scheduled.time_slot.start_time}-{scheduled.time_slot.end_time}",
            "Пара": scheduled.time_slot.name,
            "Курс": scheduled.course_name,
            "Түрі": scheduled.activity_type.value,
            "Оқытушы": faculty.name if faculty else "N/A",
            "Лауазымы": faculty.rank.value if faculty else "N/A",
            "Аудитория": room.name if room else scheduled.room_id,
            "ID": scheduled.activity_id
        })
    
    df = pd.DataFrame(data)
    
    # Күн реті бойынша сұрыптау
    day_order = {d.value: i for i, d in enumerate(DayOfWeek)}
    slot_order = {s.name: s.id for s in TimeSlot.get_standard_slots()}
    
    df['_day_order'] = df['Күн'].map(day_order)
    df['_slot_order'] = df['Пара'].map(slot_order)
    df = df.sort_values(['_day_order', '_slot_order']).drop(columns=['_day_order', '_slot_order'])
    
    return df


def create_weekly_grid(timetable: Timetable, instance: ProblemInstance, faculty_id: int = None):
    """
    Апталық кесте торын құру (визуализация үшін)
    """
    import pandas as pd
    
    time_slots = TimeSlot.get_standard_slots()
    days = list(DayOfWeek)
    
    # Бос тор құру
    grid = {day.value: {slot.name: "" for slot in time_slots} for day in days}
    
    # Деректерді толтыру
    for scheduled in timetable.scheduled_activities:
        if faculty_id is not None and scheduled.faculty_id != faculty_id:
            continue
            
        faculty = next(
            (f for f in instance.faculty if f.id == scheduled.faculty_id),
            None
        )
        room = next(
            (r for r in timetable.rooms if r.id == scheduled.room_id),
            None
        )
        
        cell_content = f"{scheduled.course_name}\n({scheduled.activity_type.value})"
        if faculty_id is None:
            cell_content += f"\n{faculty.name if faculty else 'N/A'}"
        cell_content += f"\n{room.name if room else scheduled.room_id}"
        
        grid[scheduled.day.value][scheduled.time_slot.name] = cell_content
    
    # DataFrame құру
    rows = []
    for slot in time_slots:
        row = {"Уақыт": f"{slot.start_time}-{slot.end_time}"}
        for day in days:
            row[day.value] = grid[day.value][slot.name]
        rows.append(row)
    
    return pd.DataFrame(rows)
