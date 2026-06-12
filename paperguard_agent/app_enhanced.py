"""
Enhanced Streamlit UI for PaperGuard Agent with Multi-Agent support.
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from paperguard.pipeline import run_audit
from paperguard.pipeline_agent import run_audit_with_agents
from paperguard.config import Config

st.set_page_config(
    page_title="PaperGuard Agent",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 PaperGuard Agent")
st.markdown("**面向 AI 辅助论文写作的引用幻觉与论断一致性验证智能体**")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Check API key
    if not Config.OPENAI_API_KEY:
        st.warning("⚠️ OpenAI API Key not configured")
        st.info("Set OPENAI_API_KEY in .env for Full mode")
    else:
        st.success("✅ OpenAI API Key configured")
    
    st.divider()
    
    # Architecture selection
    st.subheader("🏗️ Architecture")
    architecture = st.radio(
        "Select execution mode:",
        ["Multi-Agent System 🤖", "Functional Pipeline ⚙️"],
        help="Multi-Agent: True agent-based system\nFunctional: Traditional pipeline"
    )
    
    use_agents = architecture.startswith("Multi-Agent")
    
    if use_agents:
        st.info("✨ Using Multi-Agent Architecture")
        st.markdown("""
        **Agents:**
        - 🧠 SupervisorAgent (Coordinator)
        - 📄 ParserAgent (Paper parsing)
        - 🔍 CitationVerifierAgent (External DB)
        - ✅ ClaimVerifierAgent (LLM verification)
        """)
    else:
        st.info("⚙️ Using Functional Pipeline")
    
    st.divider()
    st.subheader("About")
    st.markdown("""
    **检测能力:**
    - ✓ 虚构引用
    - ✓ 元数据错误
    - ✓ 引用完整性
    - ✓ 论断一致性
    - ✓ 过强论断
    """)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📤 Upload Paper")
    paper_file = st.file_uploader(
        "Upload manuscript (.md, .txt, .tex, .pdf)",
        type=["md", "txt", "tex", "pdf"],
        help="Upload your paper draft (supports PDF, Markdown, LaTeX)"
    )

    bib_file = st.file_uploader(
        "Upload BibTeX (optional)",
        type=["bib"],
        help="Optional: Upload .bib for better parsing"
    )

with col2:
    st.subheader("⚙️ Settings")
    mode = st.selectbox(
        "Audit Mode",
        ["Fast", "Standard", "Full"],
        index=1,
        help="Fast: consistency | Standard: +metadata | Full: +claims"
    )
    
    max_claims = st.slider(
        "Max Claims",
        5, 50, 10,
        help="Maximum claims to verify (Full mode)"
    )

# Run audit button
if st.button("🚀 Run Audit", type="primary", disabled=not paper_file, use_container_width=True):
    with st.spinner(f"Running {mode} audit with {architecture}..."):
        try:
            # Read files based on type
            file_extension = paper_file.name.split('.')[-1].lower()

            if file_extension == 'pdf':
                # Handle PDF files
                try:
                    import PyPDF2
                    import io

                    pdf_bytes = paper_file.read()
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))

                    text_pages = []
                    for page in pdf_reader.pages:
                        text_pages.append(page.extract_text())

                    paper_content = '\n'.join(text_pages)

                    if not paper_content.strip():
                        st.error("❌ PDF appears to be empty or text extraction failed")
                        st.stop()

                    st.success(f"✅ Extracted {len(pdf_reader.pages)} pages from PDF")

                    # DEBUG: Show extraction results
                    with st.expander("🔍 PDF Extraction Debug"):
                        st.write(f"Total text length: {len(paper_content)} chars")
                        st.write(f"First 500 chars:")
                        st.code(paper_content[:500])
                        st.write(f"Last 500 chars:")
                        st.code(paper_content[-500:])

                        # Check for References
                        if 'eferences' in paper_content.lower():
                            idx = paper_content.lower().find('eferences')
                            st.success(f"✅ Found 'eferences' at position {idx}")
                            st.code(paper_content[max(0, idx-100):idx+200])
                        else:
                            st.error("❌ 'eferences' keyword not found in extracted text!")

                except ImportError:
                    st.error("❌ PDF support requires PyPDF2. Run: pip install PyPDF2")
                    st.stop()
                except Exception as e:
                    st.error(f"❌ PDF extraction failed: {e}")
                    st.stop()
            else:
                # Handle text-based files
                paper_content = paper_file.read().decode('utf-8')

            bib_content = bib_file.read().decode('utf-8') if bib_file else None

            # Validate paper content
            if not paper_content or not paper_content.strip():
                st.error("❌ Paper content is empty")
                st.stop()

            # Run audit (agent-based or functional)
            if use_agents:
                st.info("🤖 Executing Multi-Agent System...")
                report = run_audit_with_agents(paper_content, bib_content, mode, max_claims)
            else:
                st.info("⚙️ Executing Functional Pipeline...")
                report = run_audit(paper_content, bib_content, mode, max_claims)
            
            st.success("✅ Audit completed!")
            
            # Summary metrics
            st.divider()
            st.subheader("📊 Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            total_issues = len(report.issues)
            high_issues = sum(1 for i in report.issues if i.severity == "HIGH")
            medium_issues = sum(1 for i in report.issues if i.severity == "MEDIUM")
            low_issues = sum(1 for i in report.issues if i.severity == "LOW")
            
            col1.metric("Total Issues", total_issues)
            col2.metric("🔴 High", high_issues)
            col3.metric("🟡 Medium", medium_issues)
            col4.metric("🟢 Low", low_issues)
            
            # Show agent traces if using multi-agent
            if use_agents and hasattr(report, 'agent_traces'):
                st.divider()
                st.subheader("🤖 Agent Execution Traces")
                
                for idx, trace in enumerate(report.agent_traces, 1):
                    with st.expander(f"Agent {idx}: {trace[0]['agent']} ({trace[0]['role']})"):
                        for step in trace:
                            st.json({
                                "timestamp": step["timestamp"],
                                "type": step["type"],
                                "data": step["data"]
                            })
            
            # Issues table
            st.divider()
            st.subheader("🔍 Detected Issues")
            
            if report.issues:
                for idx, issue in enumerate(report.issues, 1):
                    severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
                    
                    with st.expander(
                        f"{severity_emoji[issue.severity]} [{issue.severity}] {issue.issue_type} - {issue.location}"
                    ):
                        st.markdown(f"**Location:** {issue.location}")
                        st.markdown(f"**Original Text:**")
                        st.code(issue.original_text, language=None)
                        
                        st.markdown(f"**Diagnosis:** {issue.diagnosis}")
                        
                        if issue.evidence:
                            st.markdown("**Evidence:**")
                            for ev in issue.evidence:
                                st.markdown(f"- {ev}")
                        
                        st.markdown(f"**Recommendation:** {issue.recommendation}")
                        
                        if issue.verifier_trace:
                            with st.expander("🔬 Verification Trace"):
                                st.json(issue.verifier_trace)
            else:
                st.success("🎉 No issues detected!")
            
            # Download report
            st.divider()
            report_md = report.to_markdown()
            st.download_button(
                label="📥 Download Audit Report",
                data=report_md,
                file_name="paperguard_audit_report.md",
                mime="text/markdown",
                use_container_width=True
            )
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.exception(e)

# Demo section
st.divider()
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("🧪 Try Demo")
    st.markdown("Demo paper contains 8 intentional errors:")
    st.markdown("E1: Fabricated reference | E2: Wrong year | E3: Wrong DOI | E4: Missing reference")
with col2:
    if st.button("📂 Load Demo Info", use_container_width=True):
        st.info("Upload: `data/demo_bad_paper.md`")
