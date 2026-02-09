from django.apps import apps
from django.shortcuts import render
from django.http import HttpResponse
import google.generativeai as genai
from django.shortcuts import render
from django.db import connection
import os
os.environ["GOOGLE_API_USE_MTLS_ENDPOINT"] = "never"

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-2.5-flash')
def get_current_schema():
    # 1. We find only the tables in YOUR app (e.g., 'sampletTestApp')
    # This automatically excludes internal Django tables!
    app_models = apps.get_app_config('sampletTestApp').get_models()
    
    schema_info = "You are a SQL expert. Use these tables only:\n"
    for model in app_models:
        # Get the actual database table name (e.g., sampletTestApp_student)
        table_name = model._meta.db_table
        # Get all column names
        fields = [field.name for field in model._meta.fields]
        schema_info += f"- Table: {table_name}, Columns: {fields}\n"
    
    return schema_info

def members(request):
    results = None
    sql_query = ""
    error = None
    is_er_diagram = False
    if request.method == "POST":
        user_prompt = request.POST.get('prompt')
        dynamic_schema = get_current_schema()

            # STRICTOR SYSTEM PROMPT: Forces raw SQL output
        system_instructions = f"""
        {dynamic_schema}
        ### SYSTEM CONTEXT
        {dynamic_schema}

        ### CRITICAL RULES (Do not ignore)
        1. **Format**: Return ONLY raw SQL. No markdown, no backticks, no conversation.
        2. **Table Listing**: If the user asks for 'all tables', return: 
        SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'sampletTestApp%';
        3. **Filtering**: DO NOT show tables starting with 'django_', 'auth_', or 'sqlite_'.
        5. VISUALIZATION RULE: If the user asks for a 'chart', 'graph', or 'pie chart', your SQL query MUST return exactly TWO columns: 
            - Column 1: A string category (e.g., region, name).
            - Column 2: A numerical value (e.g., total_sales, count).
        6. If user asks for 'ER Diagram', generate a Mermaid erDiagram.
            1. Start with 'erDiagram'.
            2. Define tables and their relationships based on the schema.
            3. Return ONLY the Mermaid code. No markdown or text.

        ### ACTION PRIORITY (Creation vs Insertion)
        4. **Prefer Existing**: Before writing a 'CREATE TABLE' query, check the schema above. If a table with that name exists, use 'INSERT INTO' instead.
        5. **No Duplicates**: Never generate 'CREATE TABLE' if the table name is already in the schema.
        6. **Value Intent**: If you see specific data (e.g., 'Alice', 95), ALWAYS generate 'INSERT INTO' rather than 'CREATE'.
        7. **Pragma Limit**: ONLY use 'PRAGMA table_info' for "structure", "columns", or "schema" requests. Never use it for data entry.
        """

        try:
            # 1. Ask Gemini to write the SQL
            response = model.generate_content(f"{system_instructions}\n\nQuestion: {user_prompt}")
            sql_query = response.text.strip().replace('```sql', '').replace('```', '').split(';')[0] + ';'
            raw_output = response.text.strip().replace('```mermaid', '').replace('```', '')
            # 2. Run the SQL on your database
            if raw_output.lower().startswith("erdiagram"):
                is_er_diagram = True
                results = raw_output # Pass Mermaid code directly to results
            else:
                with connection.cursor() as cursor:
                    cursor.execute(sql_query)
                    # Check if the query returned data (like a SELECT query)
                    if "erDiagram" in sql_query:
                        is_er_diagram = True
                        results = sql_query # Pass the mermaid code to the template
                    if cursor.description:
                        columns = [col[0] for col in cursor.description]
                        rows = cursor.fetchall()
                        results = [dict(zip(columns, row)) for row in rows]
                    else:
                        # For CREATE or INSERT, show a success message
                        results = [{"Status": "Success", "Message": "Command executed successfully"}]
                
        except Exception as e:
            error = str(e)

    return render(request, 'homePage.html', {
        'results': results, 
        'sql': sql_query, 
        'error': error
    })

# Create your views here.
