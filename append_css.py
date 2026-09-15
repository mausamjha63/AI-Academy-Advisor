css_append = """
/* 6. Strict Mobile Overflow Fixes */
@media (max-width: 768px) {
    html, body {
        overflow-x: hidden;
        width: 100%;
        max-width: 100%;
    }
    .app-container, .main-content-wrapper {
        width: 100%;
        max-width: 100vw;
        min-width: 0;
        overflow-x: hidden;
    }
    .top-header {
        width: 100%;
        max-width: 100%;
        min-width: 0;
        box-sizing: border-box;
    }
    .header-left, .header-right {
        max-width: 100%;
        min-width: 0;
    }
    .header-left h2 {
        white-space: normal;
        word-wrap: break-word;
    }
    .header-left p {
        white-space: normal;
        word-wrap: break-word;
    }
    .search-box {
        max-width: 100%;
        min-width: 0;
    }
    .student-selector {
        max-width: 100%;
        min-width: 0;
        flex-wrap: wrap;
    }
    .student-selector select {
        max-width: 100%;
        min-width: 0;
        text-overflow: ellipsis;
    }
    
    .card, .content-container, .main-scroll-area {
        max-width: 100%;
        min-width: 0;
        box-sizing: border-box;
    }
    
    .table-responsive {
        max-width: 100%;
        width: 100%;
    }
}

/* 7. Chat Layout Mobile Override */
@media (max-width: 1024px) {
    .chat-layout {
        display: flex;
        flex-direction: column;
        height: auto;
    }
    .chat-side, .chat-main, .evidence-panel {
        width: 100%;
        max-width: 100%;
        min-width: 0;
        box-sizing: border-box;
    }
    .chat-history-sidebar {
        height: auto !important;
        position: static !important;
        max-height: none !important;
    }
    .chat-main {
        height: 60vh !important;
    }
    .message {
        max-width: 90%;
        word-wrap: break-word;
        overflow-wrap: anywhere;
    }
}
"""

with open('static/css/styles.css', 'a') as f:
    f.write(css_append)
