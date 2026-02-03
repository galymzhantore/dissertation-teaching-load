import random
from typing import List, Tuple
import pandas as pd

from backend.core.models import (
    Faculty, CourseActivity, ProblemInstance,
    FacultyRank, ActivityType
)

class DataGenerator:
    FIRST_NAMES = [
        "Айгуль", "Асель", "Жанар", "Дина", "Сауле",
        "Ерлан", "Арман", "Нурлан", "Бауыржан", "Марат",
        "Алия", "Камила", "Назым", "Асия", "Жания"
    ]
    
    LAST_NAMES = [
        "Абдуллаев", "Смагулов", "Оспанова", "Жумабаев", "Сейтова",
        "Нурмуханов", "Алимбетов", "Касымова", "Ерланов", "Жаксылыков"
    ]
    
    COURSE_PREFIXES = ["CS", "MATH", "PHYS", "ENG", "BUS"]
    COURSE_NAMES = {
        "CS": ["Бағдарламалау I", "Деректер құрылымы", "Алгоритмдер", "Дерекқор жүйелері", "Веб-әзірлеу"],
        "MATH": ["Математикалық талдау", "Сызықтық алгебра", "Дискретті математика", "Статистика", "Ықтималдықтар теориясы"],
        "PHYS": ["Физика I", "Физика II", "Термодинамика", "Кванттық механика", "Оптика"],
        "ENG": ["Академиялық жазу", "Техникалық ағылшын тілі", "Әдебиет", "Коммуникация", "Презентация дағдылары"],
        "BUS": ["Микроэкономика", "Маркетинг", "Бухгалтерлік есеп", "Менеджмент", "Қаржы"]
    }
    
    def __init__(self, seed: int = 42):
        random.seed(seed)
        self.seed = seed
    
    def generate_faculty_name(self) -> str:
        first = random.choice(self.FIRST_NAMES)
        last = random.choice(self.LAST_NAMES)
        return f"{first} {last}"
    
    def generate_faculty(self, count: int, avg_target_load: float = None) -> List[Faculty]:
        faculty_list = []
        
        rank_distribution = [
            (FacultyRank.PROFESSOR, 0.05),
            (FacultyRank.ASSOCIATE_PROFESSOR, 0.10),
            (FacultyRank.ASSISTANT_PROFESSOR, 0.15),
            (FacultyRank.SENIOR_LECTURER, 0.20),
            (FacultyRank.SENIOR_TEACHER, 0.20),
            (FacultyRank.TEACHER, 0.20),
            (FacultyRank.ADVISOR, 0.05),
            (FacultyRank.TEACHER_ENGLISH, 0.05)
        ]
        
        special_roles = []
        if count > 10:
            special_roles.append(FacultyRank.DEAN)
        if count > 15:
            special_roles.append(FacultyRank.ADMIN)
            
        load_constraints = {
            FacultyRank.PROFESSOR: 500,
            FacultyRank.ASSOCIATE_PROFESSOR: 550,
            FacultyRank.ASSISTANT_PROFESSOR: 550,
            FacultyRank.SENIOR_LECTURER: 600,
            FacultyRank.SENIOR_TEACHER: 600,
            FacultyRank.TEACHER: 650,
            FacultyRank.ADVISOR: 250,
            FacultyRank.TEACHER_ENGLISH: 400,
            FacultyRank.DEAN: 300,
            FacultyRank.ADMIN: 300
        }
        
        for i in range(count):
            if i < len(special_roles):
                selected_rank = special_roles[i]
            else:
                r = random.random()
                cumulative = 0
                selected_rank = FacultyRank.TEACHER
                for rank, prob in rank_distribution:
                    cumulative += prob
                    if r <= cumulative:
                        selected_rank = rank
                        break
            
            base_load = load_constraints[selected_rank]
            
            # Ережеге сәйкес: жылдық максимум 680 сағаттан аспауы керек
            MAX_ANNUAL_LOAD = 680
            
            if selected_rank == FacultyRank.ADMIN:
                target_load = random.uniform(100, 250)
                max_load = 300
            elif selected_rank == FacultyRank.DEAN:
                # Декандар 0.5 ставкаға дейін алуы мүмкін
                target_load = random.uniform(200, 340)
                max_load = min(340, MAX_ANNUAL_LOAD / 2)
            else:
                target_load = base_load + random.uniform(0, 30)
                max_load = min(target_load * random.uniform(1.1, 1.15), MAX_ANNUAL_LOAD)
            
            faculty = Faculty(
                id=i + 1,
                name=self.generate_faculty_name(),
                rank=selected_rank,
                target_load=round(target_load, 1),
                max_load=round(max_load, 1)
            )
            
            faculty_list.append(faculty)
        
        return faculty_list
    
    def generate_courses(
        self, 
        count: int, 
        lectures_per_course: int = 2,
        practicals_per_course: int = 3
    ) -> List[CourseActivity]:
        activities = []
        
        for course_num in range(1, count + 1):
            dept = random.choice(self.COURSE_PREFIXES)
            course_id = f"{dept}{100 + course_num}"
            course_name = random.choice(self.COURSE_NAMES[dept])
            
            for section in range(1, lectures_per_course + 1):
                hours = random.choice([30, 45, 60])
                students = random.randint(80, 200)
                
                activity = CourseActivity(
                    id=f"{course_id}_L{section}",
                    course_id=course_id,
                    course_name=course_name,
                    activity_type=ActivityType.LECTURE,
                    section_number=section,
                    hours=hours,
                    student_count=students,
                    required_rank=FacultyRank.SENIOR_LECTURER
                )
                activities.append(activity)
            
            for section in range(1, practicals_per_course + 1):
                hours = random.choice([15, 30, 45])
                students = random.randint(20, 40)
                
                activity = CourseActivity(
                    id=f"{course_id}_P{section}",
                    course_id=course_id,
                    course_name=course_name,
                    activity_type=ActivityType.PRACTICAL,
                    section_number=section,
                    hours=hours,
                    student_count=students,
                    required_rank=FacultyRank.TEACHER
                )
                activities.append(activity)
        
        return activities
    
    def generate_supervision_activities(
        self,
        faculty: List[Faculty],
        bachelor_students: int = 30,
        master_students: int = 15,
        nirm_projects: int = 10
    ) -> List[CourseActivity]:
        """
        Жетекшілік белсенділіктерін генерациялау
        
        Нормативтер (сағат/студент):
        - Бакалавр дипломдық жұмыс: 20 сағат
        - Магистр диссертация: 40 сағат  
        - НИРМ/ЭИР: 25 сағат
        """
        activities = []
        
        # Жетекші бола алатын оқытушылар (профессор, доцент, аға оқытушы)
        qualified_supervisors = [
            f for f in faculty 
            if f.rank in [
                FacultyRank.PROFESSOR,
                FacultyRank.ASSOCIATE_PROFESSOR,
                FacultyRank.ASSISTANT_PROFESSOR,
                FacultyRank.SENIOR_LECTURER,
                FacultyRank.SENIOR_TEACHER
            ]
        ]
        
        # Магистр жетекшілігі үшін тек профессор/доцент
        master_supervisors = [
            f for f in faculty
            if f.rank in [
                FacultyRank.PROFESSOR,
                FacultyRank.ASSOCIATE_PROFESSOR,
                FacultyRank.ASSISTANT_PROFESSOR
            ]
        ]
        
        if not qualified_supervisors:
            qualified_supervisors = faculty[:5]
        if not master_supervisors:
            master_supervisors = faculty[:3]
        
        # Бакалавр жетекшілігі (20 сағат/студент)
        for i in range(bachelor_students):
            supervisor = random.choice(qualified_supervisors)
            activity = CourseActivity(
                id=f"THESIS_B{i+1}",
                course_id="THESIS_BACHELOR",
                course_name=f"Бакалавр дипломдық жұмыс #{i+1}",
                activity_type=ActivityType.BACHELOR_THESIS,
                section_number=i + 1,
                hours=20,  # 20 сағат/студент
                student_count=1,
                required_rank=FacultyRank.SENIOR_LECTURER
            )
            activities.append(activity)
        
        # Магистр жетекшілігі (40 сағат/студент)
        for i in range(master_students):
            supervisor = random.choice(master_supervisors)
            activity = CourseActivity(
                id=f"THESIS_M{i+1}",
                course_id="THESIS_MASTER",
                course_name=f"Магистр диссертация #{i+1}",
                activity_type=ActivityType.MASTER_THESIS,
                section_number=i + 1,
                hours=40,  # 40 сағат/студент
                student_count=1,
                required_rank=FacultyRank.ASSISTANT_PROFESSOR
            )
            activities.append(activity)
        
        # НИРМ/ЭИР (25 сағат/жоба)
        for i in range(nirm_projects):
            supervisor = random.choice(master_supervisors)
            activity = CourseActivity(
                id=f"NIRM_{i+1}",
                course_id="NIRM_EIR",
                course_name=f"НИРМ/ЭИР жобасы #{i+1}",
                activity_type=ActivityType.RESEARCH_NIRM,
                section_number=i + 1,
                hours=25,  # 25 сағат/жоба
                student_count=random.randint(2, 5),
                required_rank=FacultyRank.ASSISTANT_PROFESSOR
            )
            activities.append(activity)
        
        return activities
    
    def generate_qualification_matrix(
        self,
        faculty: List[Faculty],
        activities: List[CourseActivity],
        qualification_rate: float = 0.4
    ) -> dict:
        matrix = {}
        
        courses_activities = {}
        for activity in activities:
            if activity.course_id not in courses_activities:
                courses_activities[activity.course_id] = []
            courses_activities[activity.course_id].append(activity)
        
        courses = list(courses_activities.keys())
        
        rank_hierarchy = [
            FacultyRank.ADMIN,
            FacultyRank.ADVISOR,
            FacultyRank.TEACHER,
            FacultyRank.TEACHER_ENGLISH,
            FacultyRank.SENIOR_TEACHER,
            FacultyRank.SENIOR_LECTURER,
            FacultyRank.ASSISTANT_PROFESSOR,
            FacultyRank.ASSOCIATE_PROFESSOR,
            FacultyRank.PROFESSOR,
            FacultyRank.DEAN
        ]
        
        for f in faculty:
            num_qualified_courses = int(len(courses) * qualification_rate)
            num_qualified_courses = max(2, num_qualified_courses)
            
            qualified_courses = random.sample(courses, min(num_qualified_courses, len(courses)))
            f.qualified_courses = qualified_courses
            
            for activity in activities:
                is_qualified = False
                
                if activity.course_id in qualified_courses:
                    if activity.required_rank:
                        try:
                            faculty_rank_level = rank_hierarchy.index(f.rank)
                            required_rank_level = rank_hierarchy.index(activity.required_rank)
                            is_qualified = faculty_rank_level >= required_rank_level
                        except ValueError:
                            is_qualified = True
                    else:
                        is_qualified = True
                
                matrix[(f.id, activity.id)] = is_qualified
                
                if is_qualified:
                    f.preferences[activity.id] = random.randint(5, 10)
        
        for activity in activities:
            has_qualified = False
            for f in faculty:
                if matrix.get((f.id, activity.id), False):
                    has_qualified = True
                    break
            
            if not has_qualified:
                potential_faculty = []
                if activity.required_rank:
                    req_idx = rank_hierarchy.index(activity.required_rank)
                    potential_faculty = [
                        f for f in faculty 
                        if rank_hierarchy.index(f.rank) >= req_idx
                    ]
                else:
                    potential_faculty = faculty
                
                if not potential_faculty:
                    potential_faculty = faculty
                
                chosen_f = random.choice(potential_faculty)
                
                if activity.course_id not in chosen_f.qualified_courses:
                    chosen_f.qualified_courses.append(activity.course_id)
                
                matrix[(chosen_f.id, activity.id)] = True
                chosen_f.preferences[activity.id] = random.randint(5, 10)
        
        return matrix
    
    def generate_instance(
        self,
        size: str = "small",
        name: str = None
    ) -> ProblemInstance:
        size_configs = {
            "small": {
                "faculty_count": 15,
                "course_count": 10,
                "lectures_per": 2,
                "practicals_per": 2,
                "avg_load": 360,
                "bachelor_students": 20,
                "master_students": 8,
                "nirm_projects": 5
            },
            "medium": {
                "faculty_count": 35,
                "course_count": 25,
                "lectures_per": 2,
                "practicals_per": 3,
                "avg_load": 360,
                "bachelor_students": 50,
                "master_students": 20,
                "nirm_projects": 12
            },
            "large": {
                "faculty_count": 70,
                "course_count": 50,
                "lectures_per": 3,
                "practicals_per": 4,
                "avg_load": 360,
                "bachelor_students": 100,
                "master_students": 40,
                "nirm_projects": 25
            }
        }
        
        if size not in size_configs:
            raise ValueError(f"Invalid size: {size}. Must be 'small', 'medium', or 'large'")
        
        config = size_configs[size]
        
        faculty = self.generate_faculty(config["faculty_count"], config["avg_load"])
        
        # Аудиториялық белсенділіктер
        activities = self.generate_courses(
            config["course_count"],
            config["lectures_per"],
            config["practicals_per"]
        )
        
        # Жетекшілік белсенділіктерін қосу
        supervision_activities = self.generate_supervision_activities(
            faculty,
            bachelor_students=config["bachelor_students"],
            master_students=config["master_students"],
            nirm_projects=config["nirm_projects"]
        )
        activities.extend(supervision_activities)
        
        qual_matrix = self.generate_qualification_matrix(faculty, activities)
        
        instance = ProblemInstance(
            faculty=faculty,
            activities=activities,
            qualification_matrix=qual_matrix,
            name=name or f"{size.capitalize()} Instance ({len(faculty)} faculty, {len(activities)} activities)",
            metadata={
                "size": size,
                "seed": self.seed,
                "total_demand": sum(a.hours for a in activities),
                "total_capacity": sum(f.max_load for f in faculty),
                "supervision_stats": {
                    "bachelor_students": config["bachelor_students"],
                    "master_students": config["master_students"],
                    "nirm_projects": config["nirm_projects"]
                }
            }
        )
        
        return instance
    
    def export_to_csv(self, instance: ProblemInstance, output_dir: str = "data/input"):
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        faculty_data = []
        for f in instance.faculty:
            faculty_data.append({
                "id": f.id,
                "name": f.name,
                "rank": f.rank.value,
                "target_load": f.target_load,
                "max_load": f.max_load,
                "weight": f.weight
            })
        pd.DataFrame(faculty_data).to_csv(f"{output_dir}/faculty.csv", index=False)
        
        activity_data = []
        for a in instance.activities:
            activity_data.append({
                "id": a.id,
                "course_id": a.course_id,
                "course_name": a.course_name,
                "activity_type": a.activity_type.value,
                "section": a.section_number,
                "hours": a.hours,
                "students": a.student_count,
                "required_rank": a.required_rank.value if a.required_rank else None
            })
        pd.DataFrame(activity_data).to_csv(f"{output_dir}/activities.csv", index=False)
        
        qual_data = []
        for (f_id, a_id), is_qual in instance.qualification_matrix.items():
            if is_qual:
                qual_data.append({
                    "faculty_id": f_id,
                    "activity_id": a_id,
                    "qualified": is_qual
                })
        pd.DataFrame(qual_data).to_csv(f"{output_dir}/qualifications.csv", index=False)
        
        print(f"✅ Exported instance data to {output_dir}/")


if __name__ == "__main__":
    generator = DataGenerator(seed=42)
    
    print("Generating test instances...")
    for size in ["small", "medium", "large"]:
        instance = generator.generate_instance(size)
        print(f"\n{size.upper()} Instance:")
        print(f"  Faculty: {len(instance.faculty)}")
        print(f"  Activities: {len(instance.activities)}")
        print(f"  Total demand: {instance.get_total_demand()} hours")
        print(f"  Total capacity: {instance.get_total_capacity()} hours")
        feasible, msg = instance.check_capacity_feasibility()
        print(f"  Feasibility: {msg}")
        
        generator.export_to_csv(instance, f"data/input/{size}")
    
    print("\n✅ Data generation complete!")
