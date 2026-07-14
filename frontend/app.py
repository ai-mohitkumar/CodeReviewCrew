from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st


# ---------------------------------------------------------
# Application Configuration
# ---------------------------------------------------------

try:
    API_URL = st.secrets["API_URL"]
except (KeyError, FileNotFoundError):
    API_URL = os.getenv(
        "API_URL",
        "http://127.0.0.1:8000/api/run",
    )

REQUEST_TIMEOUT_SECONDS = (10, 300)


# ---------------------------------------------------------
# Demo Requirements
# ---------------------------------------------------------

DEMO_CASES = {
    "Custom Requirement": "",
    "Addition": (
        "Create a Python function named add that accepts two numbers "
        "and returns their sum."
    ),
    "Prime Number": (
        "Create a Python function named is_prime that checks whether "
        "a number is prime."
    ),
    "Odd or Even": (
        "Create a Python function named check_even_odd that returns "
        "'even' for even numbers and 'odd' for odd numbers."
    ),
    "Palindrome": (
        "Create a Python function named is_palindrome that checks "
        "whether a string is a palindrome."
    ),
    "Bug Detection + Automatic Repair": (
        "Create a Python function named modulo that returns the "
        "remainder of two numbers."
    ),
}


WORKFLOW_STAGES = [
    "User Requirement",
    "Coder",
    "Reviewer",
    "Tester",
    "Executor",
    "Report",
    "End",
]


# ---------------------------------------------------------
# Streamlit Page Configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="CodeReviewCrew",
    page_icon=":material/terminal:",
    layout="wide",
)


# ---------------------------------------------------------
# Session State
# ---------------------------------------------------------

def initialize_state() -> None:
    st.session_state.setdefault("final_report", None)
    st.session_state.setdefault(
        "selected_demo",
        "Custom Requirement",
    )
    st.session_state.setdefault(
        "requirement_input",
        "",
    )


def apply_demo_requirement() -> None:
    selected_demo = st.session_state.get(
        "selected_demo",
        "Custom Requirement",
    )

    st.session_state["requirement_input"] = DEMO_CASES.get(
        selected_demo,
        "",
    )


# ---------------------------------------------------------
# UI Helper Functions
# ---------------------------------------------------------

def status_badge(report: dict[str, Any] | None) -> str:

    if not report:
        return ":blue-badge[Ready]"

    if report.get("tests_passed"):
        return ":green-badge[Passing]"

    if report.get("status") == "failed":
        return ":red-badge[Needs repair]"

    return ":orange-badge[In progress]"


def workflow_text() -> str:
    return " -> ".join(WORKFLOW_STAGES)


def render_stage_flow() -> None:

    stage_columns = st.columns(len(WORKFLOW_STAGES))

    for column, stage in zip(
        stage_columns,
        WORKFLOW_STAGES,
    ):

        with column:
            st.caption(stage.upper())


def render_review(review_feedback: Any) -> None:

    if isinstance(review_feedback, dict):

        approved = bool(
            review_feedback.get("approved")
        )

        quality_score = review_feedback.get(
            "quality_score"
        )

        badge = (
            ":green-badge[Approved]"
            if approved
            else ":orange-badge[Revision recommended]"
        )

        st.markdown(badge)

        if quality_score is not None:

            st.metric(
                "Quality score",
                f"{quality_score}/100",
            )

        issues = review_feedback.get("issues") or []

        suggestions = (
            review_feedback.get("suggestions") or []
        )

        if issues:

            st.write("Issues")

            for issue in issues:
                st.write(f"- {issue}")

        if suggestions:

            st.write("Suggestions")

            for suggestion in suggestions:
                st.write(f"- {suggestion}")

        if not issues and not suggestions:

            st.success(
                "The reviewer did not return any blocking findings.",
                icon=":material/check_circle:",
            )

        return

    if review_feedback:

        st.write(review_feedback)

    else:

        st.info(
            "No review findings were returned.",
            icon=":material/info:",
        )


def render_agent_summary(
    agent_summary: dict[str, str],
) -> None:

    for agent_name, summary in agent_summary.items():

        with st.container(border=True):

            st.caption(agent_name.upper())

            st.write(
                summary
                or "No summary was recorded for this agent."
            )


def render_iteration_card(
    iteration_data: dict[str, Any],
    index: int,
) -> None:

    iteration_number = iteration_data.get(
        "iteration",
        index + 1,
    )

    test_result = (
        iteration_data.get("test_result") or {}
    )

    passed = bool(
        test_result.get("passed")
    )

    headline = "Passed" if passed else "Failed"

    with st.container(border=True):

        col1, col2 = st.columns(
            [0.7, 0.3],
            vertical_alignment="center",
        )

        with col1:

            st.subheader(
                f"Iteration {iteration_number}"
            )

            st.caption(
                "Generated implementation, review snapshot, "
                "tests, and output."
            )

        with col2:

            st.markdown(
                ":green-badge[Passed]"
                if passed
                else ":red-badge[Failed]"
            )

        summary_cols = st.columns(3)

        summary_cols[0].metric(
            "Result",
            headline.upper(),
        )

        summary_cols[1].metric(
            "Return code",
            str(
                test_result.get(
                    "returncode",
                    "n/a",
                )
            ),
        )

        summary_cols[2].metric(
            "Stdout lines",
            str(
                len(
                    str(
                        test_result.get(
                            "stdout",
                            "",
                        )
                    ).splitlines()
                )
            ),
        )

        code_col, review_col = st.columns(2)

        with code_col:

            st.caption(
                "Generated implementation"
            )

            st.code(
                iteration_data.get("code") or "",
                language="python",
            )

        with review_col:

            st.caption("Reviewer snapshot")

            render_review(
                iteration_data.get("review")
            )

        test_col, output_col = st.columns(2)

        with test_col:

            st.caption("Generated tests")

            st.code(
                iteration_data.get("tests") or "",
                language="python",
            )

        with output_col:

            st.caption("Execution output")

            output_parts = []

            stdout = test_result.get("stdout")

            stderr = test_result.get("stderr")

            if stdout:
                output_parts.append(str(stdout))

            if stderr:
                output_parts.append(str(stderr))

            if output_parts:

                st.code(
                    "\n".join(output_parts),
                    language="text",
                )

            else:

                st.info(
                    "No execution output was recorded.",
                    icon=":material/info:",
                )


# ---------------------------------------------------------
# Initialize Application
# ---------------------------------------------------------

initialize_state()

report = st.session_state.final_report


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:

    st.title("Control center")

    st.caption(
        "Multi-agent software engineering workflow"
    )

    st.markdown(
        status_badge(report)
    )

    st.caption("Pipeline")

    for stage in WORKFLOW_STAGES:
        st.write(f"- {stage}")

    st.caption("Workspace")

    st.write(f"Backend: `{API_URL}`")

    st.write(
        "Interactive Streamlit review surface"
    )

    st.write(
        "Built for code, tests, and repair loops"
    )


# ---------------------------------------------------------
# Hero Section
# ---------------------------------------------------------

hero_col, signal_col = st.columns(
    [1.4, 0.6],
    vertical_alignment="top",
)


with hero_col:

    st.title("CodeReviewCrew")

    st.write(
        "A professional control surface for generating code, "
        "reviewing it, running tests, and inspecting automatic "
        "repair iterations."
    )

    st.caption(
        workflow_text()
    )


with signal_col:

    with st.container(border=True):

        st.caption("Current signal")

        st.markdown(
            status_badge(report)
        )

        st.write(
            "One requirement goes through coder, reviewer, "
            "tester, executor, and report stages."
        )


# ---------------------------------------------------------
# Requirement Input
# ---------------------------------------------------------

request_col, overview_col = st.columns(
    [1.2, 0.8],
    vertical_alignment="top",
)


with request_col:

    with st.container(border=True):

        st.subheader("Run a workflow")

        st.caption(
            "Choose a demo or enter a custom Python requirement. "
            "The request is sent to the backend only when you run it."
        )

        selected_demo = st.selectbox(
            "Demonstration case",
            options=list(DEMO_CASES.keys()),
            key="selected_demo",
            on_change=apply_demo_requirement,
        )

        requirement = st.text_area(
            "Programming requirement",
            placeholder=(
                "Example: Create a Python function that checks "
                "whether a number is prime."
            ),
            height=180,
            key="requirement_input",
        )

        run_agents = st.button(
            "Run agents",
            type="primary",
            icon=":material/play_arrow:",
            use_container_width=True,
        )


with overview_col:

    with st.container(border=True):

        st.subheader("System overview")

        st.caption(
            "What this workspace is optimized to show"
        )

        st.write(
            "- Deterministic demo cases for clear walkthroughs"
        )

        st.write(
            "- Review findings with quality scoring"
        )

        st.write(
            "- Generated pytest coverage and execution output"
        )

        st.write(
            "- Full repair timeline when the first attempt fails"
        )

    with st.container(border=True):

        st.subheader("Workflow stages")

        st.caption(
            "Aligned to the README pipeline"
        )

        render_stage_flow()


# ---------------------------------------------------------
# Workflow Progress
# ---------------------------------------------------------

progress_container = st.container(border=True)

with progress_container:

    st.subheader("Workflow progress")

    st.caption(
        "Live run state and latest system response"
    )

    progress_placeholder = st.empty()


# ---------------------------------------------------------
# Execute Backend Request
# ---------------------------------------------------------

if run_agents:

    if not requirement.strip():

        progress_placeholder.warning(
            "Please enter a programming requirement before "
            "running the workflow.",
            icon=":material/warning:",
        )

    else:

        st.session_state.final_report = None

        progress_placeholder.warning(
            "Running User Requirement -> Coder -> Reviewer "
            "-> Tester -> Executor...",
            icon=":material/schedule:",
        )

        try:

            with st.spinner(
                "Running multi-agent workflow..."
            ):

                response = requests.post(
                    API_URL,
                    json={
                        "requirement": requirement.strip()
                    },
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )

            response.raise_for_status()

            st.session_state.final_report = (
                response.json()
            )

            report = (
                st.session_state.final_report
            )

            if report.get("tests_passed"):

                progress_placeholder.success(
                    "Workflow completed successfully. "
                    "Tests passed and the final report is ready.",
                    icon=":material/check_circle:",
                )

            else:

                progress_placeholder.error(
                    "Workflow finished with a failed final test state. "
                    "Inspect the repair iterations and report for details.",
                    icon=":material/error:",
                )


        except requests.ConnectionError:

            progress_placeholder.error(
                f"Could not connect to backend: {API_URL}",
                icon=":material/error:",
            )


        except requests.Timeout:

            progress_placeholder.error(
                "The workflow request timed out.",
                icon=":material/timer_off:",
            )


        except requests.RequestException as exc:

            progress_placeholder.error(
                f"Backend request failed: {exc}",
                icon=":material/error:",
            )


        except ValueError:

            progress_placeholder.error(
                "The backend returned an invalid JSON response.",
                icon=":material/error:",
            )


else:

    progress_placeholder.info(
        "Ready to run. Submit a requirement to populate code, "
        "review, tests, execution output, and the final report.",
        icon=":material/info:",
    )


# ---------------------------------------------------------
# Latest Report
# ---------------------------------------------------------

report = st.session_state.final_report


# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------

(
    tab_progress,
    tab_code,
    tab_review,
    tab_tests,
    tab_output,
    tab_iterations,
    tab_report,
) = st.tabs(
    [
        "Workflow Progress",
        "Generated Code",
        "Review Findings",
        "Generated Tests",
        "Test Output",
        "Repair Iterations",
        "Final Report",
    ]
)


# ---------------------------------------------------------
# Workflow Progress Tab
# ---------------------------------------------------------

with tab_progress:

    with st.container(border=True):

        st.subheader("Workflow progress")

        st.caption(
            "Summary of the current run, aligned to the README flow."
        )

        st.write(
            workflow_text()
        )

        if report:

            metric_columns = st.columns(4)

            metric_columns[0].metric(
                "Status",
                str(
                    report.get(
                        "status",
                        "unknown",
                    )
                ).upper(),
            )

            metric_columns[1].metric(
                "Tests passed",
                (
                    "YES"
                    if report.get("tests_passed")
                    else "NO"
                ),
            )

            metric_columns[2].metric(
                "Iterations used",
                str(
                    report.get(
                        "iterations_used",
                        0,
                    )
                ),
            )

            quality_score = report.get(
                "quality_score"
            )

            metric_columns[3].metric(
                "Quality score",
                (
                    f"{quality_score}/100"
                    if quality_score is not None
                    else "n/a"
                ),
            )

            info_col, reason_col = st.columns(
                [1.1, 0.9],
                vertical_alignment="top",
            )

            with info_col:

                st.subheader(
                    "Requirement summary"
                )

                st.write(
                    report.get(
                        "requirement",
                        "",
                    )
                )

            with reason_col:

                st.subheader(
                    "Termination reason"
                )

                st.write(
                    report.get(
                        "termination_reason",
                        "No termination reason returned.",
                    )
                )

        else:

            st.info(
                "Workflow progress details will appear here "
                "after a workflow run.",
                icon=":material/info:",
            )


# ---------------------------------------------------------
# Generated Code Tab
# ---------------------------------------------------------

with tab_code:

    with st.container(border=True):

        st.subheader(
            "Generated implementation"
        )

        st.caption(
            "Final code returned by the workflow"
        )

        if report:

            st.code(
                report.get(
                    "final_code",
                    "",
                ),
                language="python",
            )

        else:

            st.info(
                "Generated code will appear here "
                "after a workflow run.",
                icon=":material/code:",
            )


# ---------------------------------------------------------
# Review Tab
# ---------------------------------------------------------

with tab_review:

    with st.container(border=True):

        st.subheader(
            "Review findings"
        )

        st.caption(
            "Latest reviewer assessment"
        )

        if report:

            render_review(
                report.get(
                    "review_feedback"
                )
            )

        else:

            st.info(
                "Reviewer findings will appear here "
                "after a workflow run.",
                icon=":material/rate_review:",
            )


# ---------------------------------------------------------
# Generated Tests Tab
# ---------------------------------------------------------

with tab_tests:

    with st.container(border=True):

        st.subheader(
            "Generated tests"
        )

        st.caption(
            "Pytest coverage synthesized from the requirement"
        )

        if report:

            st.code(
                report.get(
                    "generated_tests",
                    "",
                ),
                language="python",
            )

        else:

            st.info(
                "Generated tests will appear here "
                "after a workflow run.",
                icon=":material/science:",
            )


# ---------------------------------------------------------
# Test Output Tab
# ---------------------------------------------------------

with tab_output:

    with st.container(border=True):

        st.subheader(
            "Execution output"
        )

        st.caption(
            "Stdout and stderr from the test run"
        )

        if report:

            test_output = report.get(
                "test_output",
                "",
            )

            if test_output:

                st.code(
                    test_output,
                    language="text",
                )

            else:

                st.info(
                    "No test output was returned.",
                    icon=":material/info:",
                )

        else:

            st.info(
                "Execution output will appear here "
                "after a workflow run.",
                icon=":material/terminal:",
            )


# ---------------------------------------------------------
# Repair Iterations Tab
# ---------------------------------------------------------

with tab_iterations:

    st.subheader(
        "Repair timeline"
    )

    st.caption(
        "Each executor attempt is preserved "
        "as its own checkpoint."
    )

    if report:

        iterations = (
            report.get("iterations") or []
        )

        if not iterations:

            st.info(
                "No workflow iterations were recorded.",
                icon=":material/history:",
            )

        else:

            if len(iterations) == 1:

                st.success(
                    "The implementation passed testing "
                    "on the first iteration.",
                    icon=":material/check_circle:",
                )

            else:

                st.warning(
                    f"The workflow used {len(iterations)} "
                    "iterations before producing its final state.",
                    icon=":material/build:",
                )

            for index, iteration_data in enumerate(
                iterations
            ):

                render_iteration_card(
                    iteration_data,
                    index,
                )

    else:

        st.info(
            "Repair iteration history will appear here "
            "after a workflow run.",
            icon=":material/history:",
        )


# ---------------------------------------------------------
# Final Report Tab
# ---------------------------------------------------------

with tab_report:

    if report:

        with st.container(border=True):

            st.subheader(
                "Structured final report"
            )

            st.caption(
                "Presented in the same order "
                "described in the README."
            )

            st.write(
                f"Requirement: `{report.get('requirement', '')}`"
            )

            st.write(
                f"Status: `{report.get('status', 'unknown')}`"
            )

            st.write(
                f"Tests passed: `{report.get('tests_passed', False)}`"
            )

            st.write(
                f"Iterations used: `{report.get('iterations_used', 0)}`"
            )

            st.write(
                f"Max iterations: `{report.get('max_iterations', 0)}`"
            )

            st.write(
                f"Termination reason: "
                f"`{report.get('termination_reason', '')}`"
            )


        with st.container(border=True):

            st.subheader("Final code")

            st.code(
                report.get(
                    "final_code",
                    "",
                ),
                language="python",
            )


        with st.container(border=True):

            st.subheader(
                "Review feedback"
            )

            render_review(
                report.get(
                    "review_feedback"
                )
            )


        with st.container(border=True):

            st.subheader(
                "Generated tests"
            )

            st.code(
                report.get(
                    "generated_tests",
                    "",
                ),
                language="python",
            )


        with st.container(border=True):

            st.subheader(
                "Test output"
            )

            test_output = report.get(
                "test_output",
                "",
            )

            if test_output:

                st.code(
                    test_output,
                    language="text",
                )

            else:

                st.info(
                    "No test output was returned.",
                    icon=":material/info:",
                )


        with st.container(border=True):

            st.subheader(
                "Agent summary"
            )

            render_agent_summary(
                report.get(
                    "agent_summary",
                    {},
                )
            )


        with st.container(border=True):

            st.subheader(
                "Raw final report"
            )

            st.json(report)


    else:

        st.info(
            "The final structured report will appear here "
            "after a workflow run.",
            icon=":material/description:",
        )