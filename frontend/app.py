from __future__ import annotations

import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000/api/run"
REQUEST_TIMEOUT_SECONDS = 120


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


st.set_page_config(
    page_title="CodeReviewCrew",
    page_icon="🤖",
    layout="wide",
)


st.title(
    "CodeReviewCrew — Multi-Agent Code Generation, "
    "Review & Testing Platform"
)

st.write(
    "Enter a Python programming requirement and run the "
    "multi-agent workflow."
)


selected_demo = st.selectbox(
    "Choose Demonstration Case",
    options=list(DEMO_CASES.keys()),
)

default_requirement = DEMO_CASES[selected_demo]

requirement = st.text_area(
    "Programming Requirement",
    value=default_requirement,
    placeholder=(
        "Example: Create a Python function that checks "
        "whether a number is prime."
    ),
    height=150,
)



run_agents = st.button(
    "Run Agents",
    type="primary",
    use_container_width=True,
)


st.subheader("Workflow Progress")

progress_placeholder = st.empty()

progress_placeholder.info(
    "Waiting to run: CODER → REVIEWER → TESTER → EXECUTOR → REPORT"
)


tab_code, tab_review, tab_tests, tab_output, tab_iterations, tab_report = (
    st.tabs(
        [
            "Generated Code",
            "Review Findings",
            "Generated Tests",
            "Test Output",
            "Repair Iterations",
            "Final Report",
        ]
    )
)


if "final_report" not in st.session_state:
    st.session_state.final_report = None


if run_agents:
    if not requirement.strip():
        st.warning("Please enter a programming requirement.")

    else:
        st.session_state.final_report = None

        progress_placeholder.warning(
            "Running CODER → REVIEWER → TESTER → EXECUTOR..."
        )

        try:
            with st.spinner("Running multi-agent workflow..."):
                response = requests.post(
                    API_URL,
                    json={
                        "requirement": requirement.strip(),
                    },
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )

            response.raise_for_status()

            st.session_state.final_report = response.json()

            if st.session_state.final_report.get("tests_passed"):
                progress_placeholder.success(
                    "CODER → REVIEWER → TESTER → EXECUTOR "
                    "→ REPORT → TESTS PASSED"
                )
            else:
                progress_placeholder.error(
                    "CODER → REVIEWER → TESTER → EXECUTOR "
                    "→ REPAIR ITERATIONS → REPORT"
                )

        except requests.ConnectionError:
            progress_placeholder.error(
                "Could not connect to the backend. "
                "Make sure FastAPI is running on port 8000."
            )

        except requests.Timeout:
            progress_placeholder.error(
                "The workflow request timed out."
            )

        except requests.RequestException as exc:
            progress_placeholder.error(
                f"Backend request failed: {exc}"
            )

        except ValueError:
            progress_placeholder.error(
                "The backend returned an invalid JSON response."
            )


report = st.session_state.final_report


with tab_code:
    if report:
        st.code(
            report.get("final_code", ""),
            language="python",
        )
    else:
        st.info("Generated code will appear here.")


with tab_review:
    if report:
        review_feedback = report.get("review_feedback", "")

        if review_feedback:
            st.write(review_feedback)
        else:
            st.info("No review findings were returned.")
    else:
        st.info("Reviewer findings will appear here.")


with tab_tests:
    if report:
        st.code(
            report.get("generated_tests", ""),
            language="python",
        )
    else:
        st.info("Generated pytest tests will appear here.")


with tab_output:
    if report:
        test_output = report.get("test_output", "")

        if test_output:
            st.code(test_output, language="text")
        else:
            st.info("No test output was returned.")
    else:
        st.info("Test execution output will appear here.")


with tab_iterations:
    if report:
        iterations = report.get("iterations", [])

        if not iterations:
            st.info("No workflow iterations were recorded.")

        else:
            st.subheader("Agent Repair Timeline")

            total_iterations = len(iterations)

            if total_iterations == 1:
                st.success(
                    "The generated implementation passed testing "
                    "on the first iteration."
                )
            else:
                st.warning(
                    f"The workflow used {total_iterations} iterations. "
                    "The Coder repaired the implementation after "
                    "failed tests."
                )

            for index, iteration_data in enumerate(iterations):
                iteration_number = iteration_data.get(
                    "iteration",
                    index + 1,
                )

                test_result = iteration_data.get(
                    "test_result",
                    {},
                )

                passed = bool(
                    test_result.get("passed")
                )

                if passed:
                    status_text = "PASSED"
                else:
                    status_text = "FAILED"

                st.markdown(
                    f"### Iteration {iteration_number} — {status_text}"
                )

                if not passed:
                    st.error(
                        "Tests failed. The workflow routes execution "
                        "back to the Coder for repair."
                    )
                else:
                    if iteration_number > 1:
                        st.success(
                            "The repaired implementation passed all tests."
                        )
                    else:
                        st.success(
                            "The initial implementation passed all tests."
                        )

                code = iteration_data.get("code") or ""

                st.markdown("#### Generated Implementation")

                st.code(
                    code,
                    language="python",
                )

                review = iteration_data.get("review")

                st.markdown("#### Reviewer Findings")

                if review:
                    st.write(review)
                else:
                    st.info(
                        "No reviewer snapshot was recorded "
                        "for this iteration."
                    )

                tests = iteration_data.get("tests") or ""

                st.markdown("#### Generated Tests")

                st.code(
                    tests,
                    language="python",
                )

                stdout = test_result.get("stdout", "")
                stderr = test_result.get("stderr", "")

                st.markdown("#### Test Execution Output")

                if stdout:
                    st.code(
                        stdout,
                        language="text",
                    )

                if stderr:
                    st.code(
                        stderr,
                        language="text",
                    )

                if not stdout and not stderr:
                    st.info(
                        "No execution output was recorded."
                    )

                if index < total_iterations - 1:
                    st.markdown("---")

            if (
                total_iterations >= 2
                and not iterations[0]
                .get("test_result", {})
                .get("passed", False)
                and iterations[-1]
                .get("test_result", {})
                .get("passed", False)
            ):
                st.success(
                    "Repair completed successfully: "
                    "FAILED → CODER REPAIR → PASSED"
                )

    else:
        st.info(
            "Repair iteration history will appear here."
        )



with tab_report:
    if report:
        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Status",
            str(report.get("status", "unknown")).upper(),
        )

        col2.metric(
            "Tests Passed",
            "YES" if report.get("tests_passed") else "NO",
        )

        col3.metric(
            "Iterations Used",
            report.get("iterations_used", 0),
        )

        col4.metric(
            "Max Iterations",
            report.get("max_iterations", 0),
        )

        st.subheader("Agent Summary")
        st.json(report.get("agent_summary", {}))

        st.subheader("Termination Reason")
        st.write(
            report.get(
                "termination_reason",
                "No termination reason returned.",
            )
        )

        st.subheader("Complete Final Report")
        st.json(report)

    else:
        st.info("The final structured report will appear here.")