from __future__ import annotations

import pandas as pd
import streamlit as st

from scheduler import run_edd, run_exact, run_spt, validate_tasks

st.set_page_config(page_title="Task Scheduling", page_icon="📋", layout="wide")
st.title("📋 Task Scheduling")
st.caption("مقارنة بسيطة بين خوارزميات جدولة المهام على آلة واحدة: SPT و EDD و Exact.")

SAMPLE_TASKS = pd.DataFrame([
    {"Task": "A", "Processing time (P)": 4.0, "Due date (D)": 5.0},
    {"Task": "B", "Processing time (P)": 1.0, "Due date (D)": 8.0},
    {"Task": "C", "Processing time (P)": 3.0, "Due date (D)": 4.0},
    {"Task": "D", "Processing time (P)": 2.0, "Due date (D)": 6.0},
])

if "tasks_input" not in st.session_state:
    st.session_state["tasks_input"] = SAMPLE_TASKS.copy()

st.subheader("1. إدخال المهام")
st.write("أدخل اسم كل مهمة، زمن المعالجة، وموعد التسليم. يمكنك تعديل المثال أو إضافة وحذف صفوف.")
edited_df = st.data_editor(
    st.session_state["tasks_input"], num_rows="dynamic", hide_index=True,
    use_container_width=True, key="tasks_editor",
    column_config={
        "Task": st.column_config.TextColumn("اسم المهمة", required=True),
        "Processing time (P)": st.column_config.NumberColumn("زمن المعالجة (P)", min_value=0.0001, step=1.0, format="%.2f", required=True),
        "Due date (D)": st.column_config.NumberColumn("موعد التسليم (D)", min_value=0.0, step=1.0, format="%.2f", required=True),
    },
)
st.session_state["tasks_input"] = edited_df.copy()
run_button = st.button("تشغيل خوارزميات الجدولة", type="primary", use_container_width=True)

if run_button:
    try:
        records = []
        for row_number, row in edited_df.iterrows():
            name, p, due = row.get("Task"), row.get("Processing time (P)"), row.get("Due date (D)")
            name_empty = pd.isna(name) or str(name).strip() == ""
            p_empty, due_empty = pd.isna(p), pd.isna(due)
            if name_empty and p_empty and due_empty:
                continue
            if name_empty or p_empty or due_empty:
                raise ValueError(f"السطر {row_number + 1}: أكمل اسم المهمة وزمن المعالجة وموعد التسليم.")
            records.append({"name": name, "processing_time": p, "due_date": due})

        tasks = validate_tasks(records)
        results = {"SPT": run_spt(tasks), "EDD": run_edd(tasks)}
        if len(tasks) <= 9:
            results["Exact"] = run_exact(tasks, objective="Total tardiness (ΣTj)", max_jobs=9)
            st.session_state["exact_note"] = (
                f"Exact فحص {results['Exact']['permutations_checked']:,} ترتيباً واختار الترتيب الذي يحقق أقل مجموع للتأخير (ΣTj)."
            )
        else:
            st.session_state["exact_note"] = "لم يتم تشغيل Exact لأن عدد المهام أكبر من 9. تم تشغيل SPT و EDD فقط."
        st.session_state["results"] = results
        st.session_state["task_count"] = len(tasks)
    except (ValueError, TypeError) as exc:
        st.session_state.pop("results", None)
        st.session_state.pop("exact_note", None)
        st.error(str(exc))

results = st.session_state.get("results")
if results:
    st.divider()
    st.subheader("2. نتائج المقارنة")
    st.caption(f"عدد المهام: {st.session_state.get('task_count', 0)}")
    note = st.session_state.get("exact_note", "")
    if note:
        if note.startswith("لم يتم تشغيل"):
            st.warning(note)
        else:
            st.info(note)

    labels = {"SPT": "SPT — أقصر زمن معالجة", "EDD": "EDD — أقرب موعد تسليم", "Exact": "Exact — أقل مجموع للتأخير"}
    metric_names = [
        ("Total completion time (ΣCj)", "مجموع أزمنة الإكمال ΣCj"),
        ("Maximum lateness (Lmax)", "أكبر تأخر Lmax"),
        ("Total tardiness (ΣTj)", "مجموع التأخير ΣTj"),
        ("Tardy jobs", "عدد المهام المتأخرة"),
    ]
    algorithms = list(results.keys())
    columns = st.columns(len(algorithms))
    for column, algorithm in zip(columns, algorithms):
        result = results[algorithm]
        with column:
            st.markdown(f"#### {labels[algorithm]}")
            st.markdown("**ترتيب المهام**")
            st.success(" → ".join(result["sequence"]))
            for key, label in metric_names:
                value = result["metrics"][key]
                st.metric(label, str(int(value)) if key == "Tardy jobs" else f"{value:.2f}")

    st.divider()
    st.subheader("3. تفاصيل كل خوارزمية")
    tabs = st.tabs(algorithms)
    for tab, algorithm in zip(tabs, algorithms):
        with tab:
            detail = pd.DataFrame(results[algorithm]["schedule"]).rename(columns={
                "Position": "الترتيب", "Task": "المهمة", "Processing time (P)": "زمن المعالجة (P)",
                "Due date (D)": "موعد التسليم (D)", "Start": "وقت البداية", "Completion (C)": "وقت الإكمال (C)",
                "Lateness (L)": "التأخر (L)", "Tardiness (T)": "التأخير الفعلي (T)", "On time": "في الموعد؟",
            })
            st.dataframe(detail, hide_index=True, use_container_width=True)

    st.divider()
    st.subheader("4. خلاصة المقارنة")
    st.markdown(
        "- **SPT:** يرتب المهام من أقصر زمن معالجة إلى أطول زمن، ويهدف إلى تقليل مجموع أزمنة الإكمال (ΣCj).\n"
        "- **EDD:** يرتب المهام حسب أقرب موعد تسليم، ويهدف إلى تقليل أكبر تأخر (Lmax).\n"
        "- **Exact:** يجرب جميع الترتيبات الممكنة (حتى 9 مهام)، ويختار الترتيب الذي يقلل مجموع التأخير الفعلي (ΣTj)."
    )
    export_rows = []
    for algorithm, result in results.items():
        for row in result["schedule"]:
            export_rows.append({"الخوارزمية": algorithm, **row})
    export_df = pd.DataFrame(export_rows).rename(columns={
        "Position": "الترتيب", "Task": "المهمة", "Processing time (P)": "زمن المعالجة (P)",
        "Due date (D)": "موعد التسليم (D)", "Start": "وقت البداية", "Completion (C)": "وقت الإكمال (C)",
        "Lateness (L)": "التأخر (L)", "Tardiness (T)": "التأخير الفعلي (T)", "On time": "في الموعد؟",
    })
    st.download_button("تنزيل النتائج CSV", data=export_df.to_csv(index=False).encode("utf-8-sig"), file_name="scheduling_results.csv", mime="text/csv")
else:
    st.info("أدخل المهام ثم اضغط «تشغيل خوارزميات الجدولة» لعرض المقارنة.")

with st.expander("فرضيات المسألة"):
    st.markdown("- آلة واحدة تنفذ مهمة واحدة في كل مرة.\n- جميع المهام متاحة منذ الزمن صفر.\n- لا يمكن إيقاف المهمة بعد بدء تنفيذها.\n- لا توجد أزمنة إعداد بين المهام.")
