"""
Оқу жүктемесін бөлу жүйесі - Streamlit веб-қосымшасы

Аралас бүтін санды сызықтық бағдарламалау және метаэвристикалық
алгоритмдер арқылы оқу жүктемесін автоматтандырылған оңтайландыру.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import sys
from pathlib import Path

# Add project root to path (parent of frontend directory)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.core.models import FacultyRank, ActivityType, DayOfWeek, TimeSlot
from backend.data.generator import DataGenerator
from backend.solvers.ortools_solver import ORToolsSolver
from backend.solvers.pulp_solver import PuLPSolver
from backend.solvers.genetic_solver import GeneticSolver
from backend.solvers.sa_solver import SimulatedAnnealingSolver
from backend.core.timetable_generator import (
    TimetableGenerator, create_timetable_dataframe, create_weekly_grid
)
from backend.core.official_report import create_official_load_report


# Page configuration
st.set_page_config(
    page_title="Оқу жүктемесін бөлу жүйесі",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better aesthetics
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'instance' not in st.session_state:
    st.session_state.instance = None
if 'results' not in st.session_state:
    st.session_state.results = {}
if 'timetable' not in st.session_state:
    st.session_state.timetable = None


def main():
    """Негізгі қосымшаның кіру нүктесі."""
    
    # Header
    st.markdown('<div class="main-header">Оқу жүктемесін бөлу жүйесі</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Математикалық бағдарламалау арқылы оқытушыларды автоматтандырылған тағайындау</div>',
        unsafe_allow_html=True
    )
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("### Навигация")
        
        page = st.radio(
            "Бетті таңдаңыз",
            ["Басты бет", "Деректерді генерациялау", "Оңтайландыру", "📅 Кесте", "Нәтижелер және талдау", "Жүйе туралы"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Quick stats
        if st.session_state.instance:
            st.markdown("### Ағымдағы дерек")
            st.metric("Оқытушылар", len(st.session_state.instance.faculty))
            st.metric("Пәндер", len(st.session_state.instance.activities))
            st.metric("Жалпы сұраныс", f"{st.session_state.instance.get_total_demand()} сағ")
    
    # Route to pages
    if page == "Басты бет":
        show_home_page()
    elif page == "Деректерді генерациялау":
        show_data_page()
    elif page == "Оңтайландыру":
        show_optimization_page()
    elif page == "📅 Кесте":
        show_timetable_page()
    elif page == "Нәтижелер және талдау":
        show_results_page()
    elif page == "Жүйе туралы":
        show_about_page()


def show_home_page():
    """Басты бетті көрсету."""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## Мәселеге шолу")
        
        st.markdown("""
        **Оқытушыларды тағайындау есебі (TAP)** — бұл оқытушыларды оқу
        белсенділіктеріне тиімді және әділ түрде бөлуді қамтитын NP-қиын
        комбинаторлық оңтайландыру есебі.
        
        ### Негізгі қиындықтар
        - **Әділдік**: Мақсатты оқу жүктемесінен ауытқуды азайту
        - **Шектеулер**: Біліктілікті, сыйымдылық шегін және курстарды қамтуды ескеру
        - **Күрделілік**: Үлкен кафедралар үшін экспоненциалды шешімдер кеңістігі
        
        ### Біздің тәсіл
        Бұл жүйе бірнеше оңтайландыру стратегиясын жүзеге асырады:
        
        1. **Дәл әдістер** (OR-Tools, PuLP)
           - Кепілденген оңтайлы шешімдер
           - Шағын және орта даналар үшін қолайлы
           
        2. **Метаэвристикалық әдістер** (Генетикалық алгоритм)
           - Жылдам, оңтайлыға жақын шешімдер
           - Үлкен даналар үшін масштабталады
        """)
        
    with col2:
        st.markdown("## Жылдам бастау")
        
        st.info("""
        **1-қадам**: Тест деректерін генерациялау
        
        **2-қадам**: Шешушіні конфигурациялау
        
        **3-қадам**: Оңтайландыруды іске қосу
        
        **4-қадам**: Нәтижелерді талдау
        """)
        
        if st.button("Бастау", use_container_width=True, type="primary"):
            st.session_state.current_page = "Деректерді генерациялау"
            st.rerun()
    
    # Feature highlights
    st.divider()
    st.markdown("## Мүмкіндіктер")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Математикалық дәлдік")
        st.write("Сызықтандырылған мақсаттық функциясы бар MILP тұжырымдамасы дәлелденген оңтайлы шешімдерді қамтамасыз етеді")
    
    with col2:
        st.markdown("### Әділдікке басымдық")
        st.write("Салмақталған ауытқуды минимизациялау әділ жүктеме бөлуді қамтамасыз етеді")
    
    with col3:
        st.markdown("### Кешенді талдау")
        st.write("Егжей-тегжейлі теңдік метрикалары, визуализациялар және шешушілерді салыстыру")


def show_data_page():
    """Деректерді генерациялау және жүктеу беті."""
    
    st.markdown("## Деректерді генерациялау және енгізу")
    
    tab1, tab2 = st.tabs(["Синтетикалық деректерді генерациялау", "Өз деректерін жүктеу"])
    
    with tab1:
        st.markdown("### Тест данасын генерациялау")
        
        col1, col2 = st.columns(2)
        
        with col1:
            instance_size = st.selectbox(
                "Дана өлшемі",
                ["small", "medium", "large"],
                format_func=lambda x: {"small": "Шағын", "medium": "Орташа", "large": "Үлкен"}[x],
                help="Шағын: ~15 оқытушы, Орташа: ~35 оқытушы, Үлкен: ~70 оқытушы"
            )
            
            seed = st.number_input("Кездейсоқ сан генераторы", value=42, min_value=1, max_value=10000)
        
        with col2:
            size_names = {"small": "Шағын", "medium": "Орташа", "large": "Үлкен"}
            st.info(f"""
            **{size_names[instance_size]} дана:**
            - Оқытушылар: {15 if instance_size == 'small' else (35 if instance_size == 'medium' else 70)}
            - Курстар: {10 if instance_size == 'small' else (25 if instance_size == 'medium' else 50)}
            - Белсенділіктер: ~{40 if instance_size == 'small' else (100 if instance_size == 'medium' else 210)}
            """)
        
        if st.button("Деректерді генерациялау", type="primary"):
            with st.spinner("Синтетикалық деректер генерациялануда..."):
                generator = DataGenerator(seed=seed)
                instance = generator.generate_instance(instance_size)
                st.session_state.instance = instance
                
                st.success(f"Генерацияланды: {instance.name}")
                
                # Show preview
                st.markdown("### Алдын ала қарау")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Оқытушылар саны", len(instance.faculty))
                col2.metric("Оқу белсенділіктері", len(instance.activities))
                col3.metric("Біліктілік тағайындаулары", sum(instance.qualification_matrix.values()))
                
                # Check feasibility
                # Check feasibility
                is_cap_feasible, cap_msg = instance.check_capacity_feasibility()
                is_qual_feasible, qual_msg = instance.check_qualification_feasibility()
                
                if is_cap_feasible and is_qual_feasible:
                    st.success(f"✅ Жарамды: {cap_msg}")
                else:
                    if not is_cap_feasible:
                        st.error(f"❌ Сыйымдылық мәселесі: {cap_msg}")
                    if not is_qual_feasible:
                        st.error(f"❌ Біліктілік мәселесі: {len(qual_msg)} белсенділікке оқытушы жоқ!")
                        with st.expander("Толық тізімді көру"):
                            st.write(qual_msg)

    
    with tab2:
        st.markdown("### Өз деректерін жүктеу (CSV)")
        st.info("faculty.csv, activities.csv және qualifications.csv файлдарын жүктеңіз")
        
        faculty_file = st.file_uploader("Оқытушылар CSV", type=['csv'])
        activities_file = st.file_uploader("Белсенділіктер CSV", type=['csv'])
        qual_file = st.file_uploader("Біліктілік CSV", type=['csv'])
        
        st.markdown("[CSV үлгісін жүктеу](https://example.com)")
    
    # Display current instance
    if st.session_state.instance:
        st.divider()
        st.markdown("### Ағымдағы дана мәліметтері")
        
        instance = st.session_state.instance
        
        # Faculty table
        with st.expander("Оқытушылар", expanded=False):
            faculty_df = pd.DataFrame([
                {
                    "ID": f.id,
                    "Аты-жөні": f.name,
                    "Дәрежесі": f.rank.value,
                    "Мақсатты жүктеме": f.target_load,
                    "Максималды жүктеме": f.max_load,
                    "Салмағы": f.weight
                }
                for f in instance.faculty
            ])
            st.dataframe(faculty_df, use_container_width=True)
        
        # Activities table
        with st.expander("Оқу белсенділіктері", expanded=False):
            activities_df = pd.DataFrame([
                {
                    "ID": a.id,
                    "Курс": a.course_name,
                    "Түрі": a.activity_type.value,
                    "Секция": a.section_number,
                    "Сағаттар": a.hours,
                    "Студенттер": a.student_count
                }
                for a in instance.activities
            ])
            st.dataframe(activities_df, use_container_width=True)


def show_optimization_page():
    """Шешушіні конфигурациялау және орындау беті."""
    
    st.markdown("## Оңтайландыру конфигурациясы")
    
    if not st.session_state.instance:
        st.warning("Алдымен деректерді генерациялаңыз немесе жүктеңіз!")
        return
    
    instance = st.session_state.instance
    
    # Check if instance is large
    is_large_instance = len(instance.activities) > 200
    if is_large_instance:
        st.warning(
            "⚠️ **Үлкен деректер анықталды!** (200+ белсенділік)\n\n"
            "Дәл әдістер (OR-Tools, PuLP) өте ұзақ жұмыс істеуі немесе жад жетіспеуі мүмкін. "
            "**Генетикалық алгоритм** немесе **Имитациялық жасытуды** қолдану ұсынылады."
        )
    
    # Solver selection
    st.markdown("### Шешушіні таңдау")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Дәл әдістер")
        use_ortools = st.checkbox("OR-Tools CP-SAT", value=True, help="Google компаниясының жылдам дәл шешушісі")
        use_pulp = st.checkbox("PuLP (CBC)", value=True, help="Ашық бастапқы кодты MILP шешушісі")
        
        st.markdown("#### Метаэвристикалар")
        use_genetic = st.checkbox("Генетикалық алгоритм", value=False, help="Үлкен даналар үшін эволюциялық іздеу")
        use_sa = st.checkbox("Имитациялық жасыту", value=False, help="Локальды минимумнан шыға алатын ықтималдық әдіс")
    
    with col2:
        st.markdown("#### Параметрлер")
        time_limit = st.slider("Уақыт шегі (секунд)", 10, 600, 60)
        
        if use_genetic:
            st.divider()
            st.markdown("**Генетикалық алгоритм параметрлері**")
            ga_pop_size = st.number_input("Популяция өлшемі", 50, 500, 100, 10)
            ga_generations = st.number_input("Генерациялар саны", 100, 2000, 500, 50)
            
        if use_sa:
            st.divider()
            st.markdown("**Имитациялық жасыту параметрлері**")
            sa_temp = st.number_input("Бастапқы температура", 100.0, 10000.0, 1000.0, 100.0)
            sa_cooling = st.slider("Суыту жылдамдығы", 0.8, 0.99, 0.95, 0.01)
    
    # Run optimization
    solvers_selected = use_ortools or use_pulp or use_genetic or use_sa
    if st.button("Оңтайландыруды іске қосу", type="primary", disabled=not solvers_selected):
        st.markdown("### Оңтайландыру барысы")
        
        results = {}
        
        # Run OR-Tools
        if use_ortools:
            with st.spinner("OR-Tools CP-SAT жұмыс істеуде..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("OR-Tools арқылы шешуде...")
                solver = ORToolsSolver(time_limit_seconds=time_limit)
                result = solver.solve(instance)
                
                progress_bar.progress(50)
                
                results['OR-Tools'] = result
                
                if result.is_feasible:
                    st.success(f"OR-Tools: {result.solver_status} - {result.computation_time:.2f} сек")
                else:
                    st.error(f"OR-Tools: {result.solver_status}")
                
                progress_bar.progress(100)
        
        # Run PuLP
        if use_pulp:
            with st.spinner("PuLP жұмыс істеуде..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("PuLP арқылы шешуде...")
                solver = PuLPSolver(time_limit_seconds=time_limit)
                result = solver.solve(instance)
                
                progress_bar.progress(50)
                
                results['PuLP'] = result
                
                if result.is_feasible:
                    st.success(f"PuLP: {result.solver_status} - {result.computation_time:.2f} сек")
                else:
                    st.error(f"PuLP: {result.solver_status}")
                
                progress_bar.progress(100)
        
        # Run Genetic Algorithm
        if use_genetic:
            with st.spinner("Генетикалық алгоритм жұмыс істеуде..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                status_text.text("GA эволюциясы...")
                
                solver = GeneticSolver(
                    population_size=ga_pop_size, 
                    generations=ga_generations,
                    time_limit_seconds=time_limit
                )
                result = solver.solve(instance)
                progress_bar.progress(50)
                
                results['Genetic Algo'] = result
                
                if result.is_feasible:
                    st.success(f"GA: {result.solver_status} - {result.computation_time:.2f} сек (Dev: {result.total_deviation:.1f})")
                else:
                    st.error(f"GA: {result.solver_status}")
                progress_bar.progress(100)

        # Run Simulated Annealing
        if use_sa:
            with st.spinner("Имитациялық жасыту жұмыс істеуде..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                status_text.text("Annealing...")
                
                solver = SimulatedAnnealingSolver(
                    initial_temp=sa_temp,
                    cooling_rate=sa_cooling,
                    time_limit_seconds=time_limit
                )
                result = solver.solve(instance)
                progress_bar.progress(50)
                
                results['Simulated Annealing'] = result
                
                if result.is_feasible:
                    st.success(f"SA: {result.solver_status} - {result.computation_time:.2f} сек (Dev: {result.total_deviation:.1f})")
                else:
                    st.error(f"SA: {result.solver_status}")
                progress_bar.progress(100)
        
        # Store results
        st.session_state.results = results
        
        st.success("Оңтайландыру аяқталды! Нәтижелерді Талдау бетінен қараңыз.")


def show_results_page():
    """Нәтижелерді визуализациялау және салыстыру беті."""
    
    st.markdown("## Нәтижелер және талдау")
    
    if not st.session_state.results:
        st.warning("Нәтижелер жоқ. Алдымен оңтайландыруды іске қосыңыз!")
        return
    
    results = st.session_state.results
    instance = st.session_state.instance
    
    # Summary comparison table
    st.markdown("### Шешушілерді салыстыру")
    
    comparison_data = []
    for solver_name, result in results.items():
        if result.is_feasible:
            target_loads = {f.id: f.target_load for f in instance.faculty}
            metrics = result.get_equity_metrics(target_loads)
            
            comparison_data.append({
                "Шешуші": solver_name,
                "Күй": result.solver_status,
                "Уақыт (сек)": f"{result.computation_time:.2f}",
                "Тағайындаулар": len(result.assignments),
                "Жалпы ауытқу": f"{result.total_deviation:.1f}",
                "Орташа ауытқу": f"{metrics['mean_deviation']:.1f}",
                "Макс ауытқу": f"{metrics['max_deviation']:.1f}",
                "Стд ауытқу": f"{metrics['std_deviation']:.2f}"
            })
    
    if comparison_data:
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True)
        
        # Visualization
        st.markdown("### Өнімділік визуализациясы")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Time comparison
            fig_time = px.bar(
                comparison_df,
                x="Шешуші",
                y="Уақыт (сек)",
                title="Есептеу уақытын салыстыру",
                color="Шешуші"
            )
            st.plotly_chart(fig_time, use_container_width=True)
        
        with col2:
            # Deviation comparison
            deviation_data = pd.DataFrame([
                {"Шешуші": row["Шешуші"], "Метрика": "Орташа", "Мән": float(row["Орташа ауытқу"])}
                for row in comparison_data
            ] + [
                {"Шешуші": row["Шешуші"], "Метрика": "Макс", "Мән": float(row["Макс ауытқу"])}
                for row in comparison_data
            ])
            
            fig_dev = px.bar(
                deviation_data,
                x="Шешуші",
                y="Мән",
                color="Метрика",
                barmode="group",
                title="Ауытқу метрикаларын салыстыру"
            )
            st.plotly_chart(fig_dev, use_container_width=True)
        
        # Detailed results for best solver
        st.markdown("### Егжей-тегжейлі тағайындау нәтижелері")
        
        best_solver = min(results.items(), key=lambda x: x[1].total_deviation if x[1].is_feasible else float('inf'))
        
        st.info(f"**{best_solver[0]}** шешушісінің нәтижелері көрсетілуде")
        
        result = best_solver[1]
        
        # Assignment table
        assignment_data = []
        for assign in result.assignments:
            faculty = next(f for f in instance.faculty if f.id == assign.faculty_id)
            activity = next(a for a in instance.activities if a.id == assign.activity_id)
            
            assignment_data.append({
                "Оқытушы": faculty.name,
                "Дәрежесі": faculty.rank.value,
                "Курс": activity.course_name,
                "Түрі": activity.activity_type.value,
                "Секция": activity.section_number,
                "Сағаттар": activity.hours
            })
        
        assign_df = pd.DataFrame(assignment_data)
        st.dataframe(assign_df, use_container_width=True)
        
        # Download results
        csv = assign_df.to_csv(index=False)
        st.download_button(
            label="Тағайындауларды жүктеу (CSV)",
            data=csv,
            file_name="assignments.csv",
            mime="text/csv"
        )


def show_timetable_page():
    """Апталық кесте беті - толық расписание визуализациясы."""
    
    st.markdown("## 📅 Апталық кесте")
    
    if not st.session_state.results:
        st.warning("⚠️ Кесте жасау үшін алдымен оңтайландыруды іске қосыңыз!")
        return
    
    instance = st.session_state.instance
    results = st.session_state.results
    
    # Ең жақсы нәтижені таңдау
    best_solver = min(
        results.items(), 
        key=lambda x: x[1].total_deviation if x[1].is_feasible else float('inf')
    )
    best_result = best_solver[1]
    
    if not best_result.is_feasible:
        st.error("❌ Жарамды шешім табылмады!")
        return
    
    # Кесте генерациялау
    if st.session_state.timetable is None:
        with st.spinner("📅 Кесте құрылуда..."):
            generator = TimetableGenerator()
            timetable = generator.generate_timetable(instance, best_result)
            st.session_state.timetable = timetable
    
    timetable = st.session_state.timetable
    
    # Қақтығыстарды тексеру
    conflicts = timetable.check_conflicts()
    if conflicts:
        st.warning(f"⚠️ {len(conflicts)} қақтығыс табылды")
    else:
        st.success("✅ Қақтығыстар жоқ!")
    
    # Көрініс түрін таңдау
    view_type = st.radio(
        "Көрініс түрі",
        ["📊 Жалпы кесте", "👤 Оқытушы кестесі", "🏫 Аудитория кестесі"],
        horizontal=True
    )
    
    st.divider()
    
    if view_type == "📊 Жалпы кесте":
        st.markdown("### Барлық тағайындаулар")
        
        # Толық кесте кестесі
        df = create_timetable_dataframe(timetable, instance)
        
        if not df.empty:
            # Күн бойынша фильтр
            selected_day = st.selectbox(
                "Күнді таңдаңыз",
                ["Барлығы"] + [d.value for d in DayOfWeek]
            )
            
            if selected_day != "Барлығы":
                df = df[df["Күн"] == selected_day]
            
            st.dataframe(df, use_container_width=True, height=500)
            
            # Статистика
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Барлық сабақтар", len(timetable.scheduled_activities))
            col2.metric("Аудиториялар", len(timetable.rooms))
            col3.metric("Оқытушылар", len(instance.faculty))
            col4.metric("Қақтығыстар", len(conflicts))
        else:
            st.info("Кесте бос")
    
    elif view_type == "👤 Оқытушы кестесі":
        st.markdown("### Оқытушының жеке кестесі")
        
        # Оқытушыны таңдау
        faculty_options = {f"{f.name} ({f.rank.value})": f.id for f in instance.faculty}
        selected_faculty_name = st.selectbox("Оқытушыны таңдаңыз", list(faculty_options.keys()))
        selected_faculty_id = faculty_options[selected_faculty_name]
        
        # Апталық тор
        grid_df = create_weekly_grid(timetable, instance, faculty_id=selected_faculty_id)
        
        # Стильді кесте
        st.markdown("#### Апталық кесте")
        
        # HTML кесте
        html_table = "<table style='width:100%; border-collapse: collapse;'>"
        html_table += "<tr style='background-color: #1f77b4; color: white;'>"
        html_table += "<th style='border: 1px solid #ddd; padding: 8px;'>Уақыт</th>"
        for day in DayOfWeek:
            html_table += f"<th style='border: 1px solid #ddd; padding: 8px;'>{day.value}</th>"
        html_table += "</tr>"
        
        for _, row in grid_df.iterrows():
            html_table += "<tr>"
            html_table += f"<td style='border: 1px solid #ddd; padding: 8px; font-weight: bold; background-color: #f0f2f6;'>{row['Уақыт']}</td>"
            for day in DayOfWeek:
                cell = row[day.value]
                cell_style = "border: 1px solid #ddd; padding: 8px;"
                if cell:
                    cell_style += "background-color: #e8f4ea;"
                html_table += f"<td style='{cell_style}'>{cell.replace(chr(10), '<br>') if cell else '-'}</td>"
            html_table += "</tr>"
        html_table += "</table>"
        
        st.markdown(html_table, unsafe_allow_html=True)
        
        # Оқытушы статистикасы
        faculty = next(f for f in instance.faculty if f.id == selected_faculty_id)
        faculty_schedule = timetable.get_faculty_schedule(selected_faculty_id)
        total_hours = sum(s.hours for s in faculty_schedule)
        
        st.markdown("#### Жүктеме статистикасы")
        col1, col2, col3 = st.columns(3)
        col1.metric("Мақсатты жүктеме", f"{faculty.target_load} сағ")
        col2.metric("Нақты жүктеме", f"{best_result.faculty_loads.get(selected_faculty_id, 0)} сағ")
        col3.metric("Апталық сабақтар", len(faculty_schedule))
    
    elif view_type == "🏫 Аудитория кестесі":
        st.markdown("### Аудитория толтырылуы")
        
        # Аудиторияны таңдау
        room_options = {f"{r.name} ({r.room_type.value}, {r.capacity} орын)": r.id for r in timetable.rooms}
        
        if room_options:
            selected_room_name = st.selectbox("Аудиторияны таңдаңыз", list(room_options.keys()))
            selected_room_id = room_options[selected_room_name]
            
            # Аудитория кестесі
            room_schedule = timetable.get_room_schedule(selected_room_id)
            
            if room_schedule:
                room_data = []
                for s in room_schedule:
                    faculty = next((f for f in instance.faculty if f.id == s.faculty_id), None)
                    room_data.append({
                        "Күн": s.day.value,
                        "Уақыт": f"{s.time_slot.start_time}-{s.time_slot.end_time}",
                        "Курс": s.course_name,
                        "Оқытушы": faculty.name if faculty else "N/A"
                    })
                st.dataframe(pd.DataFrame(room_data), use_container_width=True)
            else:
                st.info("Бұл аудиторияда сабақ жоқ")
        else:
            st.info("Аудиториялар жоқ")
    
    st.divider()
    
    # Экспорт
    st.markdown("### 📥 Экспорт")
    
    # Кафедра атауы
    department_name = st.text_input(
        "Кафедра атауы",
        value="Ақпараттық технологиялар",
        help="Ресми есеп үшін кафедра атауын енгізіңіз"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # CSV экспорт
        df = create_timetable_dataframe(timetable, instance)
        csv = df.to_csv(index=False)
        st.download_button(
            "📄 CSV жүктеу",
            data=csv,
            file_name="кесте.csv",
            mime="text/csv"
        )
    
    with col2:
        # Excel экспорт
        try:
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Жалпы кесте', index=False)
                
                # Оқытушылар бойынша
                for faculty in instance.faculty:
                    faculty_schedule = timetable.get_faculty_schedule(faculty.id)
                    if faculty_schedule:
                        faculty_data = []
                        for s in faculty_schedule:
                            faculty_data.append({
                                "Күн": s.day.value,
                                "Уақыт": f"{s.time_slot.start_time}-{s.time_slot.end_time}",
                                "Курс": s.course_name,
                                "Түрі": s.activity_type.value,
                                "Аудитория": s.room_id
                            })
                        pd.DataFrame(faculty_data).to_excel(
                            writer, 
                            sheet_name=faculty.name[:31],  # Excel 31 символ шегі
                            index=False
                        )
            
            excel_data = output.getvalue()
            st.download_button(
                "📊 Excel жүктеу",
                data=excel_data,
                file_name="кесте.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except ImportError:
            st.info("Excel экспорт үшін 'openpyxl' орнатыңыз: pip install openpyxl")
    
    with col3:
        # Ресми есеп
        try:
            report_data = create_official_load_report(
                instance, 
                best_result,
                department_name=department_name,
                academic_year="2024-2025"
            )
            st.download_button(
                "📋 Ресми есеп (ППС жүктемесі)",
                data=report_data,
                file_name="ппс_жуктеме_болу.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"Есеп құру қатесі: {e}")


def show_about_page():
    """Әдістеме және сілтемелер беті."""
    
    st.markdown("## Жүйе туралы ақпарат")
    
    st.markdown("""
    ### Әдістеме
    
    Бұл жүйе Оқытушыларды тағайындау есебін (TAP) шешу үшін **Аралас бүтін санды
    сызықтық бағдарламалау (MILP)** тәсілін жүзеге асырады.
    
    #### Математикалық тұжырымдама
    
    **Шешім айнымалылары:**
    - $x_{ijk}$ ∈ {0,1}: $i$ оқытушысының $j$ курсының $k$ белсенділігіне тағайындалғанын көрсететін бинарлы айнымалы
    
    **Мақсаттық функция:**
    - Минимизациялау: $Z = \\sum_i W_i \\cdot |L_i - Target_i|$
      мұнда $L_i$ — нақты жүктеме, $Target_i$ — мақсатты жүктеме
    
    **Сызықтандыру:**
    - Қосымша айнымалыларды енгізу: $d_i \\geq 0$
    - Шектеулер қосу: $d_i \\geq L_i - Target_i$ және $d_i \\geq Target_i - L_i$
    - Минимизациялау: $Z = \\sum_i W_i \\cdot d_i$
    
    **Қатаң шектеулер:**
    1. Курсты қамту: Әрбір белсенділік дәл бір оқытушыға тағайындалуы керек
    2. Жүктеме шегі: Ешбір оқытушы максималды сыйымдылықтан аспауы керек
    3. Біліктілік: Тек білікті оқытушылар курстарға тағайындалады
    
    ### Шешушілер
    
    - **OR-Tools CP-SAT**: Google компаниясының шектеулерді бағдарламалау шешушісі
    - **PuLP**: CBC/GLPK шешушілеріне арналған Python интерфейсі
    - **Болашақта**: Генетикалық алгоритм, Имитациялық жасыту
    
    ### Әдебиеттер
    
    1. Burke, E. K., & Petrovic, S. (2002). Recent research directions in automated timetabling.
    2. Schaerf, A. (1999). A survey of automated timetabling.
    3. Daskalaki, S., & Birbas, T. (2005). Efficient solutions for a university timetabling problem through integer programming.
    
    ### Автор
    
    Магистрлік диссертациялық жоба
    Х. Досмұхамедов атындағы Атырау университеті
    2025 жыл
    """)


if __name__ == "__main__":
    main()
