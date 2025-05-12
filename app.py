from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
from werkzeug.utils import secure_filename
import graphviz
import tempfile
from dotenv import load_dotenv
import logging
import uuid  # Add this import

# Initialize Flask
app = Flask(__name__)

# Store conversion results in memory
conversion_results = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY in environment variables")

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Validate request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Validate file extension
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        # Secure temporary file handling
        with tempfile.NamedTemporaryFile(delete=False, suffix='.cob') as tmp_file:
            file.save(tmp_file.name)
            with open(tmp_file.name, 'r') as f:
                cobol_content = f.read()
            
            # Validate COBOL content
            if not cobol_content.strip():
                os.unlink(tmp_file.name)  # Clean up temp file before returning
                return jsonify({'error': 'Empty file content'}), 400

            # Process with Gemini
            pseudocode = generate_pseudocode(cobol_content)
            explanation = generate_explanation(cobol_content)
            flowchart_data = generate_flowchart(cobol_content)  # First attempt with Graphviz
            
            # If Graphviz flowchart generation failed, try the fallback method
            if flowchart_data and flowchart_data.startswith('Error:'):
                logger.warning("Graphviz flowchart generation failed, trying fallback SVG method")
                fallback_svg = generate_basic_svg_flowchart(cobol_content)
                if fallback_svg:
                    flowchart_data = fallback_svg
                    logger.info("Successfully generated fallback SVG flowchart")

        # Store results and generate ID
        conversion_id = str(uuid.uuid4())
        conversion_results[conversion_id] = {
            'pseudocode': pseudocode,
            'explanation': explanation,
            'flowchart': flowchart_data  # This is either the Graphviz SVG, fallback SVG, or error message
        }
        
        # Clean up temp file after processing
        if os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)

        return jsonify({'conversion_id': conversion_id})

    except Exception as e:
        logger.error(f"Processing error: {str(e)}", exc_info=True)
        # Clean up temp file in case of error during processing
        if 'tmp_file' in locals() and os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)
        return jsonify({'error': f'Internal processing error: {str(e)}'}), 500

@app.route('/results/<conversion_id>')
def results_page(conversion_id):
    # Check if the results exist to avoid rendering the page for an invalid ID
    if conversion_id not in conversion_results:
        return "Results not found or have expired.", 404  # Or render an error template
    return render_template('results.html', conversion_id=conversion_id)

@app.route('/api/results/<conversion_id>')
def api_get_results(conversion_id):
    result = conversion_results.get(conversion_id)
    if result:
        # Optionally, remove the result after fetching to save memory if results are one-time view
        # conversion_results.pop(conversion_id, None) 
        return jsonify(result)
    else:
        return jsonify({'error': 'Results not found or expired'}), 404

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'cob', 'txt'}

def generate_pseudocode(code):
    try:
        response = model.generate_content(
            f"""Convert this COBOL code to well-structured pseudocode with these rules:
            1. Use clear section headers with numbering (1. IDENTIFICATION, 2. DATA, 3. PROCEDURE)
            2. Format variables as: [Variable Name] (Type: [type], Initial: [value])
            3. Convert PERFORM to CALL/REPEAT, IF/ELSE to modern syntax
            4. Add indentation (4 spaces) for nested logic
            5. Replace COBOL syntax with plain English equivalents
            6. Never use raw COBOL syntax in output
            
            Example Output Format:
            1. IDENTIFICATION:
               Program: [name]
               Author: [author]
            
            2. DATA:
               Variables:
               - [name] (Type: [type], Initial: [value])
            
            3. LOGIC:
               [step1]
                  [substep]
               [step2]
            
            COBOL Code:
            {code}"""
        )
        return response.text
    except Exception as e:
        logger.error(f"Pseudocode generation failed: {str(e)}")
        return "Could not generate pseudocode"

def generate_explanation(code):
    try:
        response = model.generate_content(
            f"""Explain this COBOL code with these formatting rules:
            1. Never use markdown (** or *)
            2. Use bold for key terms by writing them in ALL CAPS
            3. Keep explanations concise (3-5 sentences)
            
            COBOL Code:
            {code}"""
        )
        clean_text = response.text.replace('**', '').replace('*', '')
        return clean_text.strip()
    except Exception as e:
        logger.error(f"Explanation generation failed: {str(e)}")
        return "Could not generate explanation"

def generate_flowchart(cobol_content):
    # First, check if Graphviz is available
    try:
        import shutil
        dot_path = shutil.which('dot')
        if not dot_path:
            logger.error("Graphviz 'dot' executable not found in PATH")
            return "Error: Graphviz executable 'dot' not found in system PATH. Please install Graphviz software."

        dot = graphviz.Digraph(format='svg')
        dot.attr(rankdir='TB', fontname='Arial')
        
        # Basic program structure
        dot.node('start', 'Program Start', shape='ellipse', style='filled', fillcolor='#ffefd5')  # Lighter color
        dot.node('end', 'Program End', shape='ellipse', style='filled', fillcolor='#ffefd5')  # Lighter color
        
        # Check for divisions
        divisions = []
        if "IDENTIFICATION DIVISION" in cobol_content:
            divisions.append(('id_div', '1. Identification\\nProgram Details'))
        if "DATA DIVISION" in cobol_content:
            divisions.append(('data_div', '2. Data\\nVariables & Storage'))
        if "PROCEDURE DIVISION" in cobol_content:
            divisions.append(('proc_div', '3. Procedure\\nMain Logic'))
        
        # Add division nodes - using colors matching our app theme
        for node_id, label in divisions:
            dot.node(node_id, label, shape='box', style='rounded,filled', fillcolor='#f0f5f9')  # Light blue-grey
        
        # Connect nodes
        if len(divisions) > 0:
            dot.edge('start', divisions[0][0])
            for i in range(len(divisions)-1):
                dot.edge(divisions[i][0], divisions[i+1][0])
            dot.edge(divisions[-1][0], 'end')
        else:
            dot.edge('start', 'end')
        
        # Add simple logic flow if PROCEDURE exists
        if "PROCEDURE DIVISION" in cobol_content and 'proc_div' in [d[0] for d in divisions]:
            dot.node('process', 'Process\\nRecords', shape='box', style='filled', fillcolor='#f9ecef')  # Light pink
            dot.node('decision', 'Condition\\nCheck?', shape='diamond', style='filled', fillcolor='#fff0f5')  # Lighter pink
            dot.edge('proc_div', 'process')
            dot.edge('process', 'decision')
            dot.edge('decision', 'end', label='Done')
            dot.edge('decision', 'process', label='Continue', style='dashed')
        elif "PROCEDURE DIVISION" in cobol_content:
            if not divisions:
                dot.node('proc_direct_process', 'Procedure Logic', shape='box', style='filled', fillcolor='#f9ecef')
                dot.edge('start', 'proc_direct_process')
                dot.edge('proc_direct_process', 'end')

        try:
            logger.info("Generating SVG using Graphviz...")
            svg_output = dot.pipe().decode('utf-8')
            
            # Basic validation of the SVG output
            if not svg_output.strip().startswith('<svg'):
                logger.warning(f"Output did not start with <svg>: {svg_output[:100]}")
                return "Error: Graphviz did not produce a valid SVG. Please check your Graphviz installation."
            
            logger.info(f"Successfully generated flowchart SVG with length: {len(svg_output)}")
            return svg_output
        except graphviz.backend.execute.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8') if hasattr(e, 'stderr') and e.stderr else str(e)
            logger.error(f"Graphviz execution error: {error_msg}", exc_info=True)
            return f"Error: Failed to generate flowchart. Graphviz error: {error_msg}"
            
    except ImportError as e:
        logger.error("Required module not found", exc_info=True)
        return "Error: Missing required module. Please ensure all dependencies are installed."
    except Exception as e:
        logger.error(f"Unexpected error in flowchart generation: {str(e)}", exc_info=True)
        return f"Error: Unexpected error when generating flowchart: {str(e)}"

def generate_basic_svg_flowchart(cobol_content):
    """Generate a basic SVG flowchart without using Graphviz."""
    try:
        # Build a simple SVG manually with improved sizing
        svg_width = 800
        svg_height = 700
        
        # Check for divisions in the COBOL code
        has_id_division = "IDENTIFICATION DIVISION" in cobol_content
        has_data_division = "DATA DIVISION" in cobol_content
        has_proc_division = "PROCEDURE DIVISION" in cobol_content
        
        # Calculate number of boxes needed
        num_divisions = sum([has_id_division, has_data_division, has_proc_division])
        
        # Improved SVG building with larger text and better spacing
        svg_parts = [
            f'<svg width="{svg_width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}">',
            '<defs>',
            '  <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">',
            '    <polygon points="0 0, 10 3.5, 0 7" fill="#333"/>',
            '  </marker>',
            '</defs>',
            f'<rect width="{svg_width}" height="{svg_height}" fill="#ffffff"/>',
            # Add title to the flowchart
            f'<text x="{svg_width//2}" y="30" text-anchor="middle" font-family="Arial" font-size="24" font-weight="bold">COBOL Program Flowchart</text>',
        ]
        
        # Add circles for start/end
        start_y = 80
        end_y = svg_height - 80
        circle_radius = 40
        
        # Start node
        svg_parts.append(f'<circle cx="{svg_width//2}" cy="{start_y}" r="{circle_radius}" fill="#ffefd5" stroke="#333" stroke-width="2"/>')
        svg_parts.append(f'<text x="{svg_width//2}" y="{start_y}" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="16" font-weight="bold">Start</text>')
        
        # End node
        svg_parts.append(f'<circle cx="{svg_width//2}" cy="{end_y}" r="{circle_radius}" fill="#ffefd5" stroke="#333" stroke-width="2"/>')
        svg_parts.append(f'<text x="{svg_width//2}" y="{end_y}" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="16" font-weight="bold">End</text>')
        
        # Draw division boxes
        current_y = 180
        box_width = 220
        box_height = 80
        box_spacing = 100
        
        if num_divisions == 0:
            # Direct line from start to end
            svg_parts.append(f'<line x1="{svg_width//2}" y1="{start_y + circle_radius}" x2="{svg_width//2}" y2="{end_y - circle_radius}" stroke="#333" stroke-width="2" marker-end="url(#arrowhead)"/>')
            
            # Add a note about no divisions found
            note_y = svg_height // 2
            svg_parts.append(f'<rect x="{svg_width//2 - 150}" y="{note_y - 40}" width="300" height="80" rx="10" fill="#f9ecef" stroke="#333" stroke-width="2"/>')
            svg_parts.append(f'<text x="{svg_width//2}" y="{note_y}" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="16">No Standard COBOL Divisions Found</text>')
        else:
            last_y = start_y + circle_radius
            
            if has_id_division:
                box_x = svg_width//2 - box_width//2
                svg_parts.append(f'<rect x="{box_x}" y="{current_y}" width="{box_width}" height="{box_height}" rx="10" fill="#f0f5f9" stroke="#333" stroke-width="2"/>')
                svg_parts.append(f'<text x="{svg_width//2}" y="{current_y + box_height//2-15}" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="18" font-weight="bold">1. Identification</text>')
                svg_parts.append(f'<text x="{svg_width//2}" y="{current_y + box_height//2+15}" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="16">Program Details</text>')
                # Draw line from last element
                svg_parts.append(f'<line x1="{svg_width//2}" y1="{last_y}" x2="{svg_width//2}" y2="{current_y}" stroke="#333" stroke-width="2" marker-end="url(#arrowhead)"/>')
                last_y = current_y + box_height
                current_y += box_height + box_spacing
            
            if has_data_division:
                box_x = svg_width//2 - box_width//2
                svg_parts.append(f'<rect x="{box_x}" y="{current_y}" width="{box_width}" height="{box_height}" rx="10" fill="#f0f5f9" stroke="#333" stroke-width="2"/>')
                svg_parts.append(f'<text x="{svg_width//2}" y="{current_y + box_height//2-15}" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="18" font-weight="bold">2. Data</text>')
                svg_parts.append(f'<text x="{svg_width//2}" y="{current_y + box_height//2+15}" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="16">Variables & Storage</text>')
                # Draw line from last element
                svg_parts.append(f'<line x1="{svg_width//2}" y1="{last_y}" x2="{svg_width//2}" y2="{current_y}" stroke="#333" stroke-width="2" marker-end="url(#arrowhead)"/>')
                last_y = current_y + box_height
                current_y += box_height + box_spacing
            
            if has_proc_division:
                box_x = svg_width//2 - box_width//2
                svg_parts.append(f'<rect x="{box_x}" y="{current_y}" width="{box_width}" height="{box_height}" rx="10" fill="#f0f5f9" stroke="#333" stroke-width="2"/>')
                svg_parts.append(f'<text x="{svg_width//2}" y="{current_y + box_height//2-15}" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="18" font-weight="bold">3. Procedure</text>')
                svg_parts.append(f'<text x="{svg_width//2}" y="{current_y + box_height//2+15}" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="16">Main Logic</text>')
                # Draw line from last element
                svg_parts.append(f'<line x1="{svg_width//2}" y1="{last_y}" x2="{svg_width//2}" y2="{current_y}" stroke="#333" stroke-width="2" marker-end="url(#arrowhead)"/>')
                last_y = current_y + box_height
                
                # Add simple logic flow for procedure
                if has_proc_division:
                    proc_flow_y = current_y + box_height + 80
                    
                    # Process box
                    process_box_x = svg_width//2 - 100
                    svg_parts.append(f'<rect x="{process_box_x}" y="{proc_flow_y}" width="200" height="70" rx="5" fill="#f9ecef" stroke="#333" stroke-width="2"/>')
                    svg_parts.append(f'<text x="{svg_width//2}" y="{proc_flow_y + 35}" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="16">Process Records</text>')
                    
                    # Connect procedure to process
                    svg_parts.append(f'<line x1="{svg_width//2}" y1="{current_y + box_height}" x2="{svg_width//2}" y2="{proc_flow_y}" stroke="#333" stroke-width="2" marker-end="url(#arrowhead)"/>')
                    
                    # Decision diamond  
                    decision_y = proc_flow_y + 130
                    svg_parts.append(f'<polygon points="{svg_width//2},{decision_y-40} {svg_width//2+70},{decision_y} {svg_width//2},{decision_y+40} {svg_width//2-70},{decision_y}" fill="#fff0f5" stroke="#333" stroke-width="2"/>')
                    svg_parts.append(f'<text x="{svg_width//2}" y="{decision_y}" text-anchor="middle" dominant-baseline="middle" font-family="Arial" font-size="14">Condition?</text>')
                    
                    # Connect process to decision
                    svg_parts.append(f'<line x1="{svg_width//2}" y1="{proc_flow_y + 70}" x2="{svg_width//2}" y2="{decision_y - 40}" stroke="#333" stroke-width="2" marker-end="url(#arrowhead)"/>')
                    
                    # Decision to end (Yes/Done path)
                    svg_parts.append(f'<line x1="{svg_width//2}" y1="{decision_y + 40}" x2="{svg_width//2}" y2="{end_y - circle_radius}" stroke="#333" stroke-width="2" marker-end="url(#arrowhead)"/>')
                    svg_parts.append(f'<text x="{svg_width//2 + 15}" y="{decision_y + 60}" text-anchor="start" font-family="Arial" font-size="14">Done</text>')
                    
                    # Decision to process (No/Continue path - loop back)
                    svg_parts.append(f'<path d="M {svg_width//2 - 70} {decision_y} L {svg_width//2 - 130} {decision_y} C {svg_width//2 - 180} {decision_y} {svg_width//2 - 180} {proc_flow_y + 35} {svg_width//2 - 150} {proc_flow_y + 35} L {process_box_x} {proc_flow_y + 35}" fill="none" stroke="#333" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#arrowhead)"/>')
                    svg_parts.append(f'<text x="{svg_width//2 - 100}" y="{decision_y - 15}" text-anchor="middle" font-family="Arial" font-size="14">Continue</text>')
            else:
                # Connect last division directly to end if no procedure
                svg_parts.append(f'<line x1="{svg_width//2}" y1="{last_y}" x2="{svg_width//2}" y2="{end_y - circle_radius}" stroke="#333" stroke-width="2" marker-end="url(#arrowhead)"/>')
        
        # Add a legend
        legend_x = 50
        legend_y = svg_height - 60
        
        svg_parts.append(f'<text x="{legend_x}" y="{legend_y}" font-family="Arial" font-size="12" fill="#666">Generated flowchart based on COBOL structure analysis</text>')
        
        # Close SVG tag
        svg_parts.append('</svg>')
        
        return ''.join(svg_parts)
    
    except Exception as e:
        logger.error(f"Error in fallback SVG generation: {str(e)}", exc_info=True)
        return None

if __name__ == '__main__':
    app.run(debug=True)