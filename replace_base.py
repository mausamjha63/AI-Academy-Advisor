import re

with open('templates/base.html', 'r') as f:
    content = f.read()

# 1. Add hamburger button to header-left
header_left_old = """                <div class="header-left">
                    <h2>{% block header_title %}Overview{% endblock %}</h2>"""
header_left_new = """                <div class="header-left">
                    <button type="button" class="hamburger-btn" onclick="document.querySelector('.sidebar').classList.add('sidebar-open'); document.querySelector('.sidebar-overlay').classList.add('active');">
                        <svg width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
                    </button>
                    <h2>{% block header_title %}Overview{% endblock %}</h2>"""
content = content.replace(header_left_old, header_left_new)

# 2. Add sidebar overlay
sidebar_old = """        <!-- Sidebar -->
        <aside class="sidebar">"""
sidebar_new = """        <!-- Sidebar Overlay -->
        <div class="sidebar-overlay" onclick="document.querySelector('.sidebar').classList.remove('sidebar-open'); document.querySelector('.sidebar-overlay').classList.remove('active');"></div>
        <!-- Sidebar -->
        <aside class="sidebar">"""
content = content.replace(sidebar_old, sidebar_new)

with open('templates/base.html', 'w') as f:
    f.write(content)
