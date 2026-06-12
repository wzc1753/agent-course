"""
Streamlit UI for PaperGuard Agent.
"""
import streamlit as st
from pathlib import Path
import sys

# Add paperguard to path
sys.path.insert(0, str(Path(__file__).parent))

from paperguard.pipeline import run_audit
from paperguard.config import Config

st.set_page_config(
    page_title="PaperGuard Agent",
    page_icon="📄",
    layout="wide"
)

st.title("📄 PaperGuard Agent")
st.markdown("**面向 AI 辅助论文写作的引用幻觉与论断一致性验证智能体**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Check API key
    if not Config.OPENAI_API_KEY:
        st.warning("⚠️ OpenAI API Key not configured")
        st.info("Set OPENAI_API_KEY in .env file for claim verification")
    else:
        st.success("✅ OpenAI API Key configured")
    
    st.divider()
    st.subheader("About")
    st.markdown("""
    PaperGuard detects:
    - 虚构引用
    - 元数据错误  
    - 引用不支持论断
    - 过强论断
    - 引用完整性问题
    """)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📤 Upload Paper")
    paper_file = st.file_uploader(
        "Upload manuscript (.md, .txt, .tex)",
        type=["md", "txt", "tex"],
        help="Upload your paper draft"
    )
    
    bib_file = st.file_uploader(
        "Upload BibTeX (optional)",
        type=["bib"],
        help="Optional: Upload .bib file for better reference parsing"
    )

with col2:
    st.subheader("⚙️ Settings")
    mode = st.selectbox(
        "Audit Mode",
        ["Fast", "Standard", "Full"],
        index=1,
        help="Fast: consistency only | Standard: +metadata verification | Full: +claim verification"
    )
    
    max_claims = st.slider(
        "Max Claims to Verify",
        5, 50, 10,
        help="Maximum number of claims to verify (Full mode only)"
    )

# Run audit button
if st.button("🚀 Run Audit", type="primary", disabled=not paper_file):
    with st.spinner(f"Running {mode} audit..."):
        try:
            # Read files
            paper_content = paper_file.read().decode('utf-8')
            bib_content = bib_file.read().decode('utf-8') if bib_file else None
            
            # Run audit
            report = run_audit(paper_content, bib_content, mode, max_claims)
            
            # Display results
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
            col2.metric("High Severity", high_issues, delta=None, delta_color="inverse")
            col3.metric("Medium Severity", medium_issues)
            col4.metric("Low Severity", low_issues)
            
            # Issues table
            st.divider()
            st.subheader("🔍 Detected Issues")
            
            if report.issues:
                for idx, issue in enumerate(report.issues, 1):
                    severity_color = {
                        "HIGH": "🔴",
                        "MEDIUM": "🟡", 
                        "LOW": "🟢"
                    }
                    
                    with st.expander(
                        f"{severity_color[issue.severity]} [{issue.severity}] {issue.issue_type} - {issue.location}"
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
                st.success("🎉 No issues detected! Your paper looks good.")
            
            # Download report
            st.divider()
            report_md = report.to_markdown()
            st.download_button(
                label="📥 Download Audit Report",
                data=report_md,
                file_name="paperguard_audit_report.md",
                mime="text/markdown"
            )
            
            # Show report preview
            with st.expander("📄 Report Preview"):
                st.markdown(report_md)
                
        except Exception as e:
            st.error(f"❌ Error during audit: {str(e)}")
            st.exception(e)

# Demo section
st.divider()
st.subheader("🧪 Try Demo")
st.markdown("Load the demo paper with intentional errors to see PaperGuard in action!")

if st.button("📂 Load Demo Paper"):
    demo_path = Path("data/demo_bad_paper.md")
    if demo_path.exists():
        st.info(f"Demo paper available at: {demo_path}")
        st.markdown("Upload `data/demo_bad_paper.md` using the file uploader above.")
    else:
        st.warning("Demo paper not found. Please ensure data/demo_bad_paper.md exists.")
