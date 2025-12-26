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

from backend.core.models import FacultyRank, ActivityType
from backend.data.generator import DataGenerator
from backend.solvers.ortools_solver import ORToolsSolver
from backend.solvers.pulp_solver import PuLPSolver


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
            ["Басты бет", "Деректерді генерациялау", "Оңтайландыру", "Нәтижелер және талдау", "Жүйе туралы"],
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
                is_feasible, msg = instance.check_capacity_feasibility()
                if is_feasible:
                    st.success(f"Жарамды: {msg}")
                else:
                    st.error(f"Жарамсыз: {msg}")
    
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
    
    # Solver selection
    st.markdown("### Шешушіні таңдау")
    
    col1, col2 = st.columns(2)
    
    with col1:
        use_ortools = st.checkbox("OR-Tools CP-SAT", value=True, help="Google компаниясының жылдам дәл шешушісі")
        use_pulp = st.checkbox("PuLP (CBC)", value=True, help="Ашық бастапқы кодты MILP шешушісі")
    
    with col2:
        time_limit = st.slider("Уақыт шегі (секунд)", 10, 600, 60)
    
    # Run optimization
    if st.button("Оңтайландыруды іске қосу", type="primary", disabled=not (use_ortools or use_pulp)):
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
