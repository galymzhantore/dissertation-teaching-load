"""
Ресми есеп генераторы - Кафедраның оқу жүктемесін бөлу кестесі

Х. Досмұхамедов атындағы Атырау университетінің стандартты форматы
"""

import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from io import BytesIO

from backend.core.models import (
    ProblemInstance, OptimizationResult, 
    ActivityType, FacultyRank
)


def create_official_load_report(
    instance: ProblemInstance,
    result: OptimizationResult,
    department_name: str = "Ақпараттық технологиялар",
    academic_year: str = "2024-2025"
) -> BytesIO:
    """
    Ресми кафедра жүктеме бөлу есебін Excel форматында құру
    
    Формат: "Распределение учебно-педагогической нагрузки ППС кафедры"
    """
    
    # Оқытушылар бойынша деректерді жинау
    faculty_loads = {}
    
    for faculty in instance.faculty:
        faculty_loads[faculty.id] = {
            "faculty": faculty,
            "assignments": [],
            "total_hours": 0,
            "lecture_hours": 0,
            "practical_hours": 0,
            "lab_hours": 0,
            "seminar_hours": 0,
            "bachelor_thesis_hours": 0,
            "master_thesis_hours": 0,
            "nirm_hours": 0
        }
    
    # Тағайындауларды өңдеу
    for assignment in result.assignments:
        activity = next(
            (a for a in instance.activities if a.id == assignment.activity_id),
            None
        )
        if activity and assignment.faculty_id in faculty_loads:
            data = faculty_loads[assignment.faculty_id]
            data["assignments"].append(activity)
            data["total_hours"] += activity.hours
            
            if activity.activity_type == ActivityType.LECTURE:
                data["lecture_hours"] += activity.hours
            elif activity.activity_type == ActivityType.PRACTICAL:
                data["practical_hours"] += activity.hours
            elif activity.activity_type == ActivityType.LAB:
                data["lab_hours"] += activity.hours
            elif activity.activity_type == ActivityType.SEMINAR:
                data["seminar_hours"] += activity.hours
            elif activity.activity_type == ActivityType.BACHELOR_THESIS:
                data["bachelor_thesis_hours"] += activity.hours
            elif activity.activity_type == ActivityType.MASTER_THESIS:
                data["master_thesis_hours"] += activity.hours
            elif activity.activity_type == ActivityType.RESEARCH_NIRM:
                data["nirm_hours"] += activity.hours
    
    # Excel файлын құру
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 1. Негізгі есеп беті
        _create_main_report_sheet(writer, faculty_loads, department_name, academic_year)
        
        # 2. Толық тағайындаулар тізімі
        _create_detailed_assignments_sheet(writer, instance, result)
        
        # 3. Жүктеме статистикасы
        _create_statistics_sheet(writer, instance, result, faculty_loads)
    
    output.seek(0)
    return output


def _create_main_report_sheet(
    writer: pd.ExcelWriter,
    faculty_loads: Dict,
    department_name: str,
    academic_year: str
):
    """Негізгі ресми есеп беті"""
    
    rows = []
    row_num = 1
    
    for faculty_id, data in faculty_loads.items():
        faculty = data["faculty"]
        
        if not data["assignments"]:
            continue
        
        # Курстар бойынша топтау
        courses = {}
        for activity in data["assignments"]:
            course_key = activity.course_id
            if course_key not in courses:
                courses[course_key] = {
                    "name": activity.course_name,
                    "lecture": 0,
                    "practical": 0,
                    "lab": 0,
                    "seminar": 0,
                    "bachelor_thesis": 0,
                    "master_thesis": 0,
                    "nirm": 0,
                    "students": activity.student_count
                }
            
            if activity.activity_type == ActivityType.LECTURE:
                courses[course_key]["lecture"] += activity.hours
            elif activity.activity_type == ActivityType.PRACTICAL:
                courses[course_key]["practical"] += activity.hours
            elif activity.activity_type == ActivityType.LAB:
                courses[course_key]["lab"] += activity.hours
            elif activity.activity_type == ActivityType.SEMINAR:
                courses[course_key]["seminar"] += activity.hours
            elif activity.activity_type == ActivityType.BACHELOR_THESIS:
                courses[course_key]["bachelor_thesis"] += activity.hours
            elif activity.activity_type == ActivityType.MASTER_THESIS:
                courses[course_key]["master_thesis"] += activity.hours
            elif activity.activity_type == ActivityType.RESEARCH_NIRM:
                courses[course_key]["nirm"] += activity.hours
        
        # Әр курс бойынша жол
        for course_id, course_data in courses.items():
            # Аудиториялық жұмыс сағаттары
            classroom_hours = (
                course_data["lecture"] + 
                course_data["practical"] + 
                course_data["seminar"] + 
                course_data["lab"]
            )
            
            # Аудиториялық емес жұмыс сағаттары
            non_classroom_hours = (
                course_data["students"] * 0.25 +  # Емтихан
                course_data["bachelor_thesis"] +
                course_data["master_thesis"] +
                course_data["nirm"]
            )
            
            row = {
                "№": row_num,
                "Ф.А.Ә. оқытушы, лауазымы": f"{faculty.name}, {faculty.rank.value}",
                "Пән атауы": course_data["name"],
                "ББ атауы": "6B06103 - Ақпараттық жүйелер",  # Мысал
                "Студенттер саны": course_data["students"],
                "Оқыту тілі": "қазақ",
                "Курс": 1,
                "Семестр": 1,
                "Кредиттер саны": 3,
                "Подгруппалар": 1,
                "Дәріс (сағ)": course_data["lecture"],
                "Практ/сем (сағ)": course_data["practical"] + course_data["seminar"],
                "Зертхана (сағ)": course_data["lab"],
                "СОӨЖ (сағ)": course_data["lecture"] * 0.5,  # ~50% дәрістен
                "Аудиториялық жұмыс барлығы": classroom_hours,
                "Емтихан қабылдау": course_data["students"] * 0.25,
                "Бакалавр жетекшілігі": course_data["bachelor_thesis"],
                "Магистр жетекшілігі": course_data["master_thesis"],
                "НИРМ/ЭИР": course_data["nirm"],
                "Аудиториялық емес жұмыс барлығы": non_classroom_hours,
                "БАРЛЫҒЫ": classroom_hours + non_classroom_hours
            }
            rows.append(row)
            row_num += 1
    
    # DataFrame құру
    df = pd.DataFrame(rows)
    
    if not df.empty:
        # Excel-ге жазу
        df.to_excel(writer, sheet_name="Жүктеме бөлу", index=False, startrow=3)
        
        # Тақырып қосу
        workbook = writer.book
        worksheet = writer.sheets["Жүктеме бөлу"]
        
        title = f'Распределение учебно-педагогической нагрузки ППС кафедры "{department_name}" на {academic_year} учебный год'
        worksheet.cell(row=1, column=1, value=title)
        worksheet.merge_cells('A1:V1')


def _create_detailed_assignments_sheet(
    writer: pd.ExcelWriter,
    instance: ProblemInstance,
    result: OptimizationResult
):
    """Толық тағайындаулар тізімі"""
    
    rows = []
    for assignment in result.assignments:
        faculty = next(
            (f for f in instance.faculty if f.id == assignment.faculty_id),
            None
        )
        activity = next(
            (a for a in instance.activities if a.id == assignment.activity_id),
            None
        )
        
        if faculty and activity:
            rows.append({
                "Оқытушы": faculty.name,
                "Лауазымы": faculty.rank.value,
                "Курс коды": activity.course_id,
                "Пән атауы": activity.course_name,
                "Белсенділік түрі": activity.activity_type.value,
                "Секция": activity.section_number,
                "Сағаттар": activity.hours,
                "Студенттер саны": activity.student_count
            })
    
    df = pd.DataFrame(rows)
    df.to_excel(writer, sheet_name="Тағайындаулар", index=False)


def _create_statistics_sheet(
    writer: pd.ExcelWriter,
    instance: ProblemInstance,
    result: OptimizationResult,
    faculty_loads: Dict
):
    """Жүктеме статистикасы"""
    
    rows = []
    for faculty_id, data in faculty_loads.items():
        faculty = data["faculty"]
        actual_load = result.faculty_loads.get(faculty_id, 0)
        deviation = actual_load - faculty.target_load
        
        rows.append({
            "Оқытушы": faculty.name,
            "Лауазымы": faculty.rank.value,
            "Мақсатты жүктеме (сағ)": faculty.target_load,
            "Максималды жүктеме (сағ)": faculty.max_load,
            "Нақты жүктеме (сағ)": actual_load,
            "Ауытқу (сағ)": deviation,
            "Толтырылу (%)": round((actual_load / faculty.target_load) * 100, 1) if faculty.target_load > 0 else 0,
            "Тағайындаулар саны": len(data["assignments"]),
            "Дәріс (сағ)": data["lecture_hours"],
            "Практикалық (сағ)": data["practical_hours"],
            "Зертхана (сағ)": data["lab_hours"]
        })
    
    df = pd.DataFrame(rows)
    
    # ИТОГО жол
    if rows:
        totals = {
            "Оқытушы": "БАРЛЫҒЫ",
            "Лауазымы": "",
            "Мақсатты жүктеме (сағ)": sum(r["Мақсатты жүктеме (сағ)"] for r in rows),
            "Максималды жүктеме (сағ)": sum(r["Максималды жүктеме (сағ)"] for r in rows),
            "Нақты жүктеме (сағ)": sum(r["Нақты жүктеме (сағ)"] for r in rows),
            "Ауытқу (сағ)": sum(r["Ауытқу (сағ)"] for r in rows),
            "Толтырылу (%)": "",
            "Тағайындаулар саны": sum(r["Тағайындаулар саны"] for r in rows),
            "Дәріс (сағ)": sum(r["Дәріс (сағ)"] for r in rows),
            "Практикалық (сағ)": sum(r["Практикалық (сағ)"] for r in rows),
            "Зертхана (сағ)": sum(r["Зертхана (сағ)"] for r in rows)
        }
        df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
    
    df.to_excel(writer, sheet_name="Статистика", index=False)


def create_faculty_individual_plan(
    faculty_id: int,
    instance: ProblemInstance,
    result: OptimizationResult,
    academic_year: str = "2024-2025"
) -> BytesIO:
    """
    Оқытушының жеке жоспары (ИПР - Индивидуальный план работы)
    """
    
    faculty = next((f for f in instance.faculty if f.id == faculty_id), None)
    if not faculty:
        return BytesIO()
    
    # Тағайындауларды жинау
    assignments = []
    for assignment in result.assignments:
        if assignment.faculty_id == faculty_id:
            activity = next(
                (a for a in instance.activities if a.id == assignment.activity_id),
                None
            )
            if activity:
                assignments.append({
                    "Пән атауы": activity.course_name,
                    "Түрі": activity.activity_type.value,
                    "Сағаттар": activity.hours,
                    "Студенттер": activity.student_count
                })
    
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Негізгі ақпарат
        info_df = pd.DataFrame([{
            "Ф.А.Ә.": faculty.name,
            "Лауазымы": faculty.rank.value,
            "Оқу жылы": academic_year,
            "Мақсатты жүктеме": faculty.target_load,
            "Нақты жүктеме": result.faculty_loads.get(faculty_id, 0)
        }])
        info_df.to_excel(writer, sheet_name="ЖЖ", index=False, startrow=1)
        
        # Тағайындаулар
        if assignments:
            assign_df = pd.DataFrame(assignments)
            assign_df.to_excel(writer, sheet_name="ЖЖ", index=False, startrow=5)
    
    output.seek(0)
    return output
