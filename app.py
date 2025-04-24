from flask import Flask, request, jsonify, render_template, session
import os
import glob
from rag_engine import RAG_HUGGINGFACE, rag_engine
import uuid
import signal
import sys

app = Flask(__name__)
app.secret_key = os.urandom(24)  

DEFAULT_CSV_FOLDER = './data'



@app.route('/')
def home():
    """Home page with chat interface"""

    if 'chat_id' not in session:
        session['chat_id'] = str(uuid.uuid4())
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint for chat interaction"""
   
    data = request.json
    question = data.get('message', '')
    
    if not question:
        return jsonify({
            'status': 'error',
            'message': 'No message provided'
        }), 400
    
    chat_history = session.get('chat_history', [])
    try:
        print(question,chat_history)
        answer = rag_engine.response_query(question).split("Answer:")[-1]
        print(answer)
        chat_history.append((question, answer))
        
        if len(chat_history) > 50:  
            chat_history = chat_history[-50:]
        session['chat_history'] = chat_history
        
        return jsonify({
            'status': 'success',
            'message': answer
        })
    except Exception as e:
        print(f"Error processing query: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while processing your query'
        }), 500

@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    """Clear the chat history"""
    session['chat_history'] = []
    return jsonify({
        'status': 'success',
        'message': 'Chat history cleared'
    })

@app.route('/api/get_history', methods=['GET'])
def get_history():
    """Get the chat history"""
    chat_history = session.get('chat_history', [])
    return jsonify({
        'status': 'success',
        'history': chat_history
    })

@app.route('/api/reinitialize', methods=['POST'])
def reinitialize():
    # Already Initialized
    return True;
    

if __name__ == '__main__':
    def cleanup_handler(sig, frame):
        print("Cleaning up resources...")
        if rag_engine and hasattr(rag_engine, 'cleanup'):
            rag_engine.cleanup()
        print("Exiting program...")
        sys.exit(0)
    

    signal.signal(signal.SIGINT, cleanup_handler)
    

    app.run(debug=True, host='0.0.0.0', port=5000)