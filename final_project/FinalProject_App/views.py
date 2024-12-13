from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import ast
import re


# Function to analyze code for code smells, anti-patterns, and lexical issues
def analyze_code(code):
    tree = ast.parse(code)  # Parse the code into an AST

    # Results containers
    code_smells = []
    anti_patterns = []
    lexical_issues = []

    # Analyze AST nodes for smells and anti-patterns
    for node in ast.walk(tree):
        # Detect long functions (e.g., > 10 lines)
        if isinstance(node, ast.FunctionDef) and len(node.body) > 10:
            code_smells.append(f"Function '{node.name}' is too long (more than 10 lines).")

        # Detect large classes (e.g., > 20 methods)
        if isinstance(node, ast.ClassDef):
            method_count = sum(isinstance(n, ast.FunctionDef) for n in node.body)
            if method_count > 20:
                code_smells.append(f"Class '{node.name}' is too large (more than 20 methods).")

        # Detect nested loops (a common code smell)
        if isinstance(node, (ast.For, ast.While)) and any(
                isinstance(child, (ast.For, ast.While)) for child in node.body):
            code_smells.append(f"Nested loops detected at line {node.lineno}.")

        # Detect Singleton pattern usage (e.g., '_instance' attribute in a class)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and target.attr == '_instance':
                    anti_patterns.append("Potential Singleton pattern detected with '_instance' attribute.")

    # Analyze code lines for lexical issues
    lines = code.splitlines()
    for i, line in enumerate(lines, start=1):
        # Detect long lines (> 80 characters)
        if len(line) > 80:
            lexical_issues.append(f"Line {i}: Line exceeds 80 characters.")

        # Detect overly complex expressions (e.g., many nested parentheses)
        if len(re.findall(r'\(', line)) > 3:
            lexical_issues.append(f"Line {i}: Overly complex expression detected.")

        # Detect poorly named functions (single-letter names)
        if re.match(r'^def\s+[a-zA-Z]\(', line):
            lexical_issues.append(f"Line {i}: Poorly named function detected.")

    return code_smells, anti_patterns, lexical_issues


# Django view for rendering the frontend
def index(request):
    return render(request, 'index.html')


# Django view for handling file uploads and analysis
@csrf_exempt
def analyze_code_view(request):
    if request.method == 'POST' and request.FILES.get('codeFile'):
        # Save uploaded file
        uploaded_file = request.FILES['codeFile']
        file_path = default_storage.save(uploaded_file.name, uploaded_file)

        # Read and analyze the file
        try:
            with open(file_path, 'r') as file:
                code = file.read()
            code_smells, anti_patterns, lexical_issues = analyze_code(code)

            # Return analysis results as JSON
            return JsonResponse({
                'code_smells': code_smells,
                'anti_patterns': anti_patterns,
                'lexical_issues': lexical_issues,
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


# urls.py configuration
from django.urls import path
from myapp.views import index, analyze_code_view

urlpatterns = [
    path('', index, name='index'),
    path('analyze/', analyze_code_view, name='analyze_code'),
]

# Template file: index.html (Frontend needs to be provided separately)
